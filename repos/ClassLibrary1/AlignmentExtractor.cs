using System.Collections.Generic;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;

namespace ClassLibrary1
{
    public class AlignmentExtractor
    {

        /// <summary>
        /// 기준 Alignment와 그 프로파일, 그리고 나머지 Target Alignment들을 모두 추출합니다.
        /// </summary>
        public (Alignment BaseAlignment, Profile? BaseProfile, Dictionary<Alignment, Profile> TargetAlignments)?
            GetAllAlignments()
        {
            CivilDocument doc = CivilApplication.ActiveDocument;
            Database db = CoreApp.DocumentManager.MdiActiveDocument.Database;
            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;

            using (var tr = db.TransactionManager.StartTransaction())
            {
                // 기준 Alignment 선택
                ObjectId baseAlignmentId = PromptHelper.PromptSelectAlignment(ed);

                // 기준 Alignment/프로파일 로드
                var baseAlignment = tr.GetObject(baseAlignmentId, OpenMode.ForRead) as Alignment;
                if (baseAlignment == null)
                {
                    ed.WriteMessage("\n선택된 객체는 Alignment가 아닙니다.");
                    return null;
                }

                var baseProfile = PromptHelper.GetProfile(baseAlignment, tr);
                var results = new Dictionary<Alignment, Profile>();

                // Target Alignment 목록 생성
                foreach (ObjectId targetId in doc.GetAlignmentIds())
                {
                    if (targetId == baseAlignment.ObjectId) continue;

                    var targetAlignment = tr.GetObject(targetId, OpenMode.ForRead) as Alignment;
                    
                    Profile targetProfile = PromptHelper.GetProfile(targetAlignment, tr);
                    if (targetAlignment != null)
                        results[targetAlignment] = targetProfile;
                }

                tr.Commit();
                return (baseAlignment, baseProfile, results);
            }
        }
    }
}
