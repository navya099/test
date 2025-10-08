using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;



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
            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                try
                {
                    ObjectIdCollection SurfaceIds = doc.GetSurfaceIds();

                    Alignment baseAlignment = tr.GetObject(baseAlignmentId, OpenMode.ForRead) as Alignment;
                    Logger.Instance.SetMessage($"baseAlignment객체를 가져옴 ID :{baseAlignmentId}");
                    if (baseAlignment == null)
                    {
                        Logger.Instance.SetMessage(@"baseAlignment가 null임 :코드실행 종료");
                        return;
                    }

                    
                   
                    var demProcessor = new DEMProcessor();
                    Logger.Instance.SetMessage(@"DEMProcessor 생성 성공");
                    //autodem 생성
                    var autodem = new AUTODEM();
                    Logger.Instance.SetMessage(@"AUTODEM 생성 성공");

                    autodem.BaseAlignment = baseAlignment;
                    autodem.Step = 40;

                    autodem.ExtractStations();
                    autodem.ExtractCoordinates2D();
                    autodem.ExportTXT();

                    bool result = demProcessor.RunPythonScript();

                    if (result)
                    {
                        autodem.ReadElevationsTXT();
                        List<double> elevations = autodem.Elevations;

                        // 종단 생성
                        //종단 서비스 생성
                        var profileprovider = new ProfileService();
                        //생성전 이름 체크
                        string profilename = "지반선";
                        bool profileExists = profileprovider.IsDuplicateProfile(baseAlignment, profilename, tr);
                        if (profileExists) { profileprovider.RemoveProfile(baseAlignment, profilename, tr); }
                        //지표면 서비스 생성
                        var surfaceprovider = new SurfaceService();
                        //지표면 존재여부 확인
                        string surfacename = "Surface1";
                        ObjectId surfaceid = ObjectId.Null;
                        bool surfaceExist = surfaceprovider.HasAnyTinSurface(doc);
                        if (surfaceExist)//존재여부 확인
                        {
                            bool isduplicate = surfaceprovider.IsDuplicateTinSurface(surfacename, doc, tr);
                            if (isduplicate)//중복체크
                            {
                                //삭제 후 다시 새 지표면 생성
                                surfaceprovider.RemoveTinSurface(surfacename, doc, tr);
                                surfaceprovider.CreateTinSurface(surfacename, doc, ref surfaceid);
                            }

                        }
                        else {
                            //없으면 새로 생성
                            surfaceprovider.CreateTinSurface(surfacename, doc, ref surfaceid);
                        }
                        //지표면종단 생성
                        Profile newProfile = profileprovider.CreateSurfaceProfile(baseAlignmentId, baseAlignment, profilename, surfaceid, doc, tr);

                        // PVI 추가 (Stations + Elevations)
                        foreach (var pair in autodem.Stations.Zip(elevations, (station, elev) => (station, elev)))
                        {
                            newProfile.PVIs.AddPVI(pair.station, pair.elev);
                        }
                        Logger.Instance.SetMessage(@"지표면 종단 생성 성공");
                        Logger.Instance.SaveLogToTXT();
                    }
                    else
                    {
                        Logger.Instance.SetMessage(@"파이썬 스크립트 실행에 실패했습니다. 조건을 확인하세요");
                    }

                    tr.Commit();
                }
                catch (System.Exception ex)
                {
                    Logger.Instance.SetMessage($"코드 실행중 예외 발생 !: {ex.Message}");
                    Logger.Instance.SetMessage(ex.StackTrace);
                    tr.Abort();
                }
            }
        }
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

        
        

    }
}
