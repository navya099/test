using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.ApplicationServices.Core;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Autodesk.Civil.ApplicationServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.DatabaseServices;
using Autodesk.AutoCAD.ApplicationServices;
namespace ClassLibrary1
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize()
        {
        }

        public void Terminate()
        {
        }

        [CommandMethod("HelloCivil3D")]
        public void HelloCivil3D()
        {
            CoreApp.DocumentManager.MdiActiveDocument.Editor.WriteMessage("\nHello Civil 3D! It's a Civil 3D plugin.\n");

            CivilDocument doc = CivilApplication.ActiveDocument;
            ObjectIdCollection alignments = doc.GetAlignmentIds();
            ObjectIdCollection sites = doc.GetSiteIds();
            string docInfo = string.Format("\nThis document has {0} alignments and {1} sites.\n", alignments.Count, sites.Count);
            CoreApp.DocumentManager.MdiActiveDocument.Editor.WriteMessage(docInfo);

        }

        [CommandMethod("ExtractALLAlignmentoffset")]
        public void ExtractALLAlignmentoffset()
        {
            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            CivilDocument doc = CivilApplication.ActiveDocument;
            Database db = CoreApp.DocumentManager.MdiActiveDocument.Database;

            // 기준 Alignment 선택
            PromptEntityOptions peo = new PromptEntityOptions("\n기준 Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Alignment), true);
            PromptEntityResult per = ed.GetEntity(peo);
            if (per.Status != PromptStatus.OK) return;

            ObjectId baseAlignmentId = per.ObjectId;

            // 대상 Alignment 선택
            peo.Message = "\n거리 비교 대상 Alignment 객체를 선택하세요:";
            per = ed.GetEntity(peo);
            if (per.Status != PromptStatus.OK) return;

            ObjectId targetAlignmentId = per.ObjectId;

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                Alignment baseAlignment = tr.GetObject(baseAlignmentId, OpenMode.ForRead) as Alignment;
                Alignment targetAlignment = tr.GetObject(targetAlignmentId, OpenMode.ForRead) as Alignment;

                if (baseAlignment == null || targetAlignment == null)
                {
                    ed.WriteMessage("\n선형을 읽을 수 없습니다.");
                    return;
                }

                double interval = 25.0;
                double startStation = baseAlignment.StartingStation;
                double endStation = baseAlignment.EndingStation;

                List<string> resultLines = new List<string>();
                resultLines.Add("BaseStation\tOffsetDistance\tTargetStation");

                for (double sta = startStation; sta <= endStation; sta += interval)
                {
                    double distanceToOther = 0.0;
                    double stationOnOther = 0.0;

                    try
                    {
                        baseAlignment.DistanceToAlignment(sta, targetAlignment, ref distanceToOther, ref stationOnOther);
                        resultLines.Add($"{sta:F2}\t{distanceToOther:F2}\t{stationOnOther:F2}");
                    }
                    catch (Autodesk.Civil.PointNotOnEntityException)
                    {
                        ed.WriteMessage($"\nStation {sta:F2}는 Alignment 위에 존재하지 않습니다. 건너뜁니다.");
                    }
                    catch (System.Exception ex)
                    {
                        ed.WriteMessage($"\n예외 발생 (Station {sta:F2}): {ex.Message}");
                    }
                }

                ed.WriteMessage($"\n총 {resultLines.Count - 1}개의 오프셋 데이터를 계산했습니다.");

                foreach (string line in resultLines)
                {
                    ed.WriteMessage("\n" + line);
                }

                tr.Commit();
            }
        }



    }
}