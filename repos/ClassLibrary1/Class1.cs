using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Autodesk.Civil.ApplicationServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.DatabaseServices;
using System.ComponentModel.Design;


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

                // 베이스선형의 design profile 가져오기
                ObjectIdCollection profileIds = baseAlignment.GetProfileIds();
                Autodesk.Civil.DatabaseServices.Profile baseprofile = null;

                foreach (ObjectId profileId in profileIds)
                {
                    var profile = (Autodesk.Civil.DatabaseServices.Profile)tr.GetObject(profileId, OpenMode.ForRead);
                    if (profile.ProfileType == Autodesk.Civil.DatabaseServices.ProfileType.FG)
                    {
                        baseprofile = profile;
                        break;
                    }
                }

                double interval = 25.0;
                double startStation = baseAlignment.StartingStation;
                double endStation = baseAlignment.EndingStation;

                // BVE 변수
                int railindex = 2;

                List<string> allResults = [];
                List<string> BVETXT = [];
                allResults.Add("BaseStation,BaseElevation,TargetStation,TargetElevation,OffsetX,OffsetZ");

                foreach (ObjectId targetId in doc.GetAlignmentIds())
                {
                    if (targetId == baseAlignmentId) continue;

                    Alignment targetAlignment = tr.GetObject(targetId, OpenMode.ForRead) as Alignment;
                    if (targetAlignment == null) continue;

                    // 타겟선형의 profile 가져오기
                    ObjectIdCollection targetprofileIds = targetAlignment.GetProfileIds();
                    Autodesk.Civil.DatabaseServices.Profile targetprofile = null;
                    foreach (ObjectId profileId in targetprofileIds)
                    {
                        var profile = (Autodesk.Civil.DatabaseServices.Profile)tr.GetObject(profileId, OpenMode.ForRead);
                        if (profile.ProfileType == Autodesk.Civil.DatabaseServices.ProfileType.FG)
                        {
                            targetprofile = profile;
                            break;
                        }
                    }



                    List<string> resultLines = new List<string>();
                    List<string> bvesyntaxs = new List<string>();
                    List<(double Sta, double OffsetX, double OffsetY)> validOffsets = [];

                    string line = targetAlignment.Name;
                    resultLines.Add(line);
                    bvesyntaxs.Add($",;{line}\n");

                    double adjustedStart = Math.Ceiling(startStation / interval) * interval;
                    for (double sta = adjustedStart; sta <= endStation; sta += interval)
                    {
                        double offsetX = 0.0;
                        double offsetY = 0.0;
                        double targetSta = 0.0;
                        double current_elev = 0.0;
                        double target_elev = 0.0;
                        try
                        {
                            if (baseprofile != null)
                                {
                                current_elev = baseprofile.ElevationAt(sta);

                            }
                            else { 
                                current_elev = 0.0;
                            }
                            
                            baseAlignment.DistanceToAlignment(sta, targetAlignment, ref offsetX, ref targetSta);


                            if (targetprofile != null)
                            {
                                target_elev = targetprofile.ElevationAt(targetSta);
                                offsetY = current_elev - target_elev;
                            }
                            else
                            {
                                target_elev = 0.0;
                                offsetY = 0.0;
                            }

                            string csvLine = $"{sta:F0},{current_elev:F3},{targetSta:F3},{target_elev:F3},{-offsetX:F3},{-offsetY:F3}";
                            resultLines.Add(csvLine);

                            // offset 부호 반전한 채로 저장
                            validOffsets.Add((sta, -offsetX, -offsetY));

                        }
                        catch
                        {
                            // 무시하고 다음으로
                            continue;
                        }

                    }
                    // bvesyntaxs 구성: 마지막 줄만 RailEnd
                    if (validOffsets.Count > 0)
                    {
                        for (int i = 0; i < validOffsets.Count; i++)
                        {
                            var (sta, x, z) = validOffsets[i];
                            if (i == validOffsets.Count - 1)
                                bvesyntaxs.Add($"{sta:F0},.RailEnd {railindex};{x:F3};{z:F3};");
                            else
                                bvesyntaxs.Add($"{sta:F0},.Rail {railindex};{x:F3};{z:F3};");
                        }
                    }
                    if (saveAsOneFile)
                    {
                        allResults.AddRange(resultLines);
                        BVETXT.AddRange(bvesyntaxs);
                    }
                    else
                    {
                        string csvPath = Path.Combine(folderPath, $"{targetAlignment.Name}.csv");
                        File.WriteAllLines(csvPath, new[] { "BaseStation,BaseElevation,TargetStation,TargetElevation,OffsetX,OffsetZ" }.Concat(resultLines));
                        ed.WriteMessage($"\n{csvPath} 저장 완료.");

                        //bve문법 저장
                        string txtPath = Path.Combine(folderPath, $"{targetAlignment.Name}.txt");
                        File.WriteAllLines(txtPath, bvesyntaxs);
                    }
                    railindex++;
                }

                if (saveAsOneFile)
                {
                    string combinedcsvPath = Path.Combine(folderPath, "AllAlignmentOffsets.csv");
                    File.WriteAllLines(combinedcsvPath, allResults);
                    ed.WriteMessage($"\n모든 데이터가 {combinedcsvPath} 에 저장되었습니다.");
                    string combinedtxtPath = Path.Combine(folderPath, "AllAlignmentOffsets.txt");
                    File.WriteAllLines(combinedtxtPath, BVETXT);
                }

                tr.Commit();
            }
        }
    }
}
