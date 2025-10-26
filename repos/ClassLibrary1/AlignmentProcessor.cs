using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.ApplicationServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;

namespace ClassLibrary1
{
    public class AlignmentProcessor
    {
        private readonly AlignmentExtractor extractor = new();
        private readonly AlignmentCalculator calculator = new();
        private readonly AlignmentExporter exporter = new();

        public void ExportAllOffsets()
        {
            CivilDocument doc = CivilApplication.ActiveDocument;
            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            ed.WriteMessage("\n[INFO] 모든 노선을 처리 중...");

            // 1 프롬프트 단계 (사용자에게 계산 파라미터 입력 요청)
            string folderPath = PromptHelper.PromptFolderPath(ed);
            if (string.IsNullOrEmpty(folderPath) || !Directory.Exists(folderPath))
            {
                ed.WriteMessage($"\n경로가 유효하지 않습니다: {folderPath}");
                return;
            }

            bool saveAsOneFile = PromptHelper.PromptSaveOption(ed);
            double interval = PromptHelper.PromptInterval(ed);
            int freeobjIndex = PromptHelper.PromptFreeObjIndex(ed);
            
            int railindex = DefaultIndices.RailIndexStart;
            int railobjindex = PromptHelper.PromptRailObjIndex(ed);
            var alignmentData = extractor.GetAllAlignments();
            var alignmentResults = new List<AlignmentResult>();
            if (alignmentData == null) return;

            var (baseAlignment, baseProfile, targets) = alignmentData.Value;

            foreach (var (alignment, profile) in targets)
            {
                try
                {
                    var result = calculator.ComputeOffsetForAlignment(
                        baseAlignment,
                        baseProfile,
                        alignment,
                        profile,
                        interval
                    );

                    if (result != null)
                        alignmentResults.Add(result);
                }
                catch (Exception ex)
                {
                    // 해당 Alignment에서 문제가 발생했음을 알림
                    CoreApp.DocumentManager.MdiActiveDocument.Editor
                        .WriteMessage($"\n[WARN] {alignment.Name} 처리 중 오류 발생: {ex.Message}");
                    // continue는 생략해도 다음 루프 진행됨
                }
            }
            //BVE구문생성
            foreach (var res in alignmentResults)
            {
                res.AttachAlignmentHeader();
                res.GenerateBVELines(railindex, railobjindex); // index 1 → Alignment1
                res.GenerateFreeObjLines(railindex, freeobjIndex);
                railindex++;                      // 다음 Alignment에 2, 3 ... 할당
            }
            exporter.SavetoFile(alignmentResults, folderPath, saveAsOneFile);
            ed.WriteMessage($"\n[INFO] 총 {alignmentResults.Count}개의 노선이 처리되었습니다.");
        }
    }

}
