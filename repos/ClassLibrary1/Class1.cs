using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.ApplicationServices.Core;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Autodesk.Civil.ApplicationServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.DatabaseServices;
using Autodesk.AutoCAD.ApplicationServices;
using System.Collections.Generic;
using System.IO;

namespace ClassLibrary1
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize() { }

        public void Terminate() { }

        [CommandMethod("ExtractALLAlignmentoffset")]
        public void ExtractALLAlignmentoffset()
        {
            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            CivilDocument doc = CivilApplication.ActiveDocument;
            Database db = CoreApp.DocumentManager.MdiActiveDocument.Database;

            // 🗂️ 폴더 경로 입력 받기
            PromptStringOptions pso = new PromptStringOptions("\nCSV 파일을 저장할 폴더 경로를 입력하세요:");
            pso.AllowSpaces = true;
            PromptResult pr = ed.GetString(pso);
            if (pr.Status != PromptStatus.OK || string.IsNullOrWhiteSpace(pr.StringResult) || !Directory.Exists(pr.StringResult))
            {
                ed.WriteMessage("\n경로가 유효하지 않습니다. 작업을 중단합니다.");
                return;
            }
            string folderPath = pr.StringResult;

            // 📌 통합 저장 여부 확인
            PromptKeywordOptions pko = new PromptKeywordOptions("\n모든 오프셋 결과를 하나의 CSV 파일로 저장하시겠습니까?");
            pko.Keywords.Add("Yes");
            pko.Keywords.Add("No");
            pko.AllowNone = false;
            PromptResult keyRes = ed.GetKeywords(pko);
            bool saveAsOneFile = keyRes.StringResult == "Yes";

            // 🎯 기준 Alignment 선택
            PromptEntityOptions peo = new PromptEntityOptions("\n기준 Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Alignment), true);
            PromptEntityResult per = ed.GetEntity(peo);
            if (per.Status != PromptStatus.OK) return;

            ObjectId baseAlignmentId = per.ObjectId;

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                Alignment baseAlignment = (Alignment)tr.GetObject(baseAlignmentId, OpenMode.ForRead);
                if (baseAlignment == null) return;

                // 베이스선형의 profile 가져오기
                ObjectIdCollection profileIds = baseAlignment.GetProfileIds();
                if (profileIds.Count > 0)
                {
                    Profile profile = (Profile)tr.GetObject(profileIds[0], OpenMode.ForRead);
                }
                double interval = 25.0;
                double startStation = baseAlignment.StartingStation;
                double endStation = baseAlignment.EndingStation;

                // BVE 변수
                int railindex = 0;

                List<string> allResults = new List<string>();
                allResults.Add("BaseStation,OffsetX,Z,TargetStation,TargetName");

                foreach (ObjectId targetId in doc.GetAlignmentIds())
                {
                    if (targetId == baseAlignmentId) continue;

                    Alignment targetAlignment = tr.GetObject(targetId, OpenMode.ForRead) as Alignment;
                    if (targetAlignment == null) continue;

                    List<string> resultLines = new List<string>();

                    for (double sta = startStation; sta <= endStation; sta += interval)
                    {
                        double offsetX = 0.0, targetSta = 0.0, baseZ = 0.0, baseE = 0.0;

                        try
                        {
                            baseAlignment.DistanceToAlignment(sta, targetAlignment, ref offsetX, ref targetSta);
                            try { baseAlignment.PointLocation(sta, 0.0, ref baseE, ref baseZ); } catch { }

                            string line = $"{sta:F2},{offsetX:F2},{baseZ:F2},{targetSta:F2},{targetAlignment.Name}";
                            resultLines.Add(line);
                        }
                        catch
                        {
                            // 무시하고 다음으로
                            continue;
                        }
                    }

                    if (saveAsOneFile)
                    {
                        allResults.AddRange(resultLines);
                    }
                    else
                    {
                        string filePath = Path.Combine(folderPath, $"{targetAlignment.Name}.csv");
                        File.WriteAllLines(filePath, new[] { "BaseStation,OffsetX,Z,TargetStation" }.Concat(resultLines));
                        ed.WriteMessage($"\n{filePath} 저장 완료.");
                    }
                }

                if (saveAsOneFile)
                {
                    string combinedPath = Path.Combine(folderPath, "AllAlignmentOffsets.csv");
                    File.WriteAllLines(combinedPath, allResults);
                    ed.WriteMessage($"\n모든 데이터가 {combinedPath} 에 저장되었습니다.");
                }

                tr.Commit();
            }
        }
    }
}
