using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Exception = System.Exception;



namespace AUTO_TN_BR
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize() {}
        public void Terminate() { }

        [CommandMethod("AUTOTNBR")]

        public void AUTOTNBR()
        {


            CivilDocument doc = CivilApplication.ActiveDocument;
            Database db = CoreApp.DocumentManager.MdiActiveDocument.Database;
            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;

            ObjectId baseAlignmentId = PromptSelectAlignment(ed);
            Logger.Instance.SetMessage($"baseAlignmentId : {baseAlignmentId}");
            if (baseAlignmentId.IsNull)
            {
                Logger.Instance.SetMessage(@"baseAlignmentId가 null임 :코드실행 종료");
                return;
            }
            RunWithTransaction(db, tr =>
            {
                RunMainProcess(tr, doc, baseAlignmentId);
            });
        }

        /// <summary>
        /// AUTOCAD 메인 트랜잭션
        /// </summary>
        private void RunWithTransaction(Database db, Action<Transaction> action)
        {
            using Transaction tr = db.TransactionManager.StartTransaction();
            try
            {
                action(tr);
                tr.Commit();
            }
            catch (Exception ex)
            {
                Logger.Instance.SetMessage($"예외 발생: {ex.Message}");
                Logger.Instance.SetMessage(ex.StackTrace);
                tr.Abort();
            }
        }

        /// <summary>
        /// 메인 실행 프로세스
        /// </summary>
        private void RunMainProcess(Transaction tr, CivilDocument doc, ObjectId baseAlignmentId)
        {
            Alignment baseAlignment = GetBaseAlignment(tr, baseAlignmentId);
            if (baseAlignment == null)
            {
                Logger.Instance.SetMessage("Alignment가 null임");
                return;
            }
            //DEM처리
            var autodem = new AUTODEM();
            autodem.ProcessDEM(baseAlignment);
            Logger.Instance.SetMessage("DEM처리 성공");
            //종단생성
            var builder = new ProfileBuilder();
            Profile newProfile = builder.CreateSurfaceProfile(tr, doc, baseAlignment, autodem.Stations, autodem.Elevations);

            Logger.Instance.SetMessage("지표면 종단 생성 성공");
            //ETC 추가 기능 구현
            //NEW FEATURE...

            //완료후 로그 기록
            Logger.Instance.SaveLogToTXT();
        }

        #region 헬퍼 메소드
        /// <summary>
        /// 명령창에서 객체 선택 후 id를 반환하는 메소드
        /// </summary>
        private ObjectId PromptSelectAlignment(Editor ed)
        {
            var peo = new PromptEntityOptions("\n기준 Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Alignment), true);

            var per = ed.GetEntity(peo);
            return per.Status == PromptStatus.OK ? per.ObjectId : ObjectId.Null;
        }

        /// <summary>
        ///id로 선형 객체를 반환하는 메소드
        /// </summary>
        private Alignment GetBaseAlignment(Transaction tr, ObjectId alignmentId)
        {
            Alignment? alignment = tr.GetObject(alignmentId, OpenMode.ForRead) as Alignment;
            if (alignment != null)
                Logger.Instance.SetMessage($"baseAlignment 객체 가져옴: {alignmentId}");
            else
                Logger.Instance.SetMessage("baseAlignment가 null임 : 코드 종료");
            return alignment;
        }
        #endregion
    }
}