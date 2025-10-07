using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using CivSurface = Autodesk.Civil.DatabaseServices.Surface;

namespace AUTO_TN_BR
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize() {}
        public void Terminate() { }

        [CommandMethod("AUTOTNBR")]

        public void AUTOTNBR()
        {

            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            CivilDocument doc = CivilApplication.ActiveDocument;
            Database db = CoreApp.DocumentManager.MdiActiveDocument.Database;

            ObjectId baseAlignmentId = PromptSelectAlignment(ed);
            
            if (baseAlignmentId.IsNull) return;
            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                ObjectIdCollection SurfaceIds = doc.GetSurfaceIds();

                Alignment baseAlignment = tr.GetObject(baseAlignmentId, OpenMode.ForRead) as Alignment;
                if (baseAlignment == null) return;

                Profile baseProfile = GetProfile(baseAlignment, tr);

                var demProcessor = new DEMProcessor();

                //autodem 생성
                var autodem = new AUTODEM();

                autodem.BaseAlignment = baseAlignment;
                autodem.Step = 40;
                autodem.Editor = ed;
                autodem.ExtractStations();
                autodem.ExtractCoordinates2D();
                autodem.ExportTXT();

                bool result = demProcessor.RunPythonScript();

                if (result) {
                    autodem.ReadElevationsTXT();
                    List<double> elevations = autodem.Elevations;

                    // 종단 생성
                    //생성전 이름 체크
                    bool profileExists = IsDuplicateProfile(baseAlignment, "지반선", tr);
                    if (profileExists) { RemoveProfile(baseAlignment, "지반선", tr); }
                    Profile newProfile = CreateSurfaceProfile(baseAlignmentId, baseAlignment, "지반선", SurfaceIds[0], doc, tr);

                    // PVI 생성 (Stations + Elevations)
                    foreach (var pair in autodem.Stations.Zip(elevations, (station, elev) => (station, elev)))
                    {
                        newProfile.PVIs.AddPVI(pair.station, pair.elev);
                    }
                }
                else {
                    autodem.SetMessage("파이선 스크립트 실행이 실패했습니다.");
                }

                tr.Commit();
            }
        }
        private ObjectId PromptSelectAlignment(Editor ed)
        {
            var peo = new PromptEntityOptions("\n기준 Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Alignment), true);

            var per = ed.GetEntity(peo);
            return per.Status == PromptStatus.OK ? per.ObjectId : ObjectId.Null;
        }

        private Profile GetProfile(Alignment alignment, Transaction tr)
        {
            foreach (ObjectId profileId in alignment.GetProfileIds())
            {
                var profile = tr.GetObject(profileId, OpenMode.ForRead) as Profile;
                if (profile != null && profile.ProfileType == ProfileType.FG)
                    return profile;
            }
            return null;
        }

        internal Profile CreateLayoutProfile(ObjectId alignmentId, Alignment alignment, string profileName, CivilDocument civildoc, Transaction tr)
        {
            // 1️ 스타일 가져오기
            ObjectId profileStyleId = civildoc.Styles.ProfileStyles[0];
            ObjectId profileLabelSetId = civildoc.Styles.LabelSetStyles.ProfileLabelSetStyles[0];

            // 2️ Profile 생성 -> ObjectId 반환
            ObjectId profileId = Profile.CreateByLayout(profileName, alignmentId, alignment.LayerId, profileStyleId, profileLabelSetId);

            // 3️ Transaction 내에서 Profile 객체 가져오기
            Profile profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;

            // 4️⃣ 반환
            return profile;
        }
        internal Profile CreateSurfaceProfile(ObjectId alignmentId, Alignment alignment, string profileName, ObjectId surfaceid, CivilDocument civildoc, Transaction tr)
        
        {
            // 1️ 스타일 가져오기
            ObjectId profileStyleId = civildoc.Styles.ProfileStyles[0];
            ObjectId profileLabelSetId = civildoc.Styles.LabelSetStyles.ProfileLabelSetStyles[0];

            // 2️ Profile 생성 -> ObjectId 반환
            ObjectId profileId = Profile.CreateFromSurface(profileName, alignmentId, surfaceid,  alignment.LayerId, profileStyleId, profileLabelSetId);

            // 3️ Transaction 내에서 Profile 객체 가져오기
            Profile profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;

            // 4️⃣ 반환
            return profile;
        }

        internal void RemoveProfile(Alignment baseAlignment, string profilename, Transaction tr)
        {
            // Alignment의 모든 Profile 중 이름이 같은 것 찾기
            foreach (ObjectId profileId in baseAlignment.GetProfileIds())
            {
                Profile profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;
                if (profile != null && profile.Name == "지반선")
                {
                    profile.Erase();  // 트랜잭션 내에서 삭제
                    profile = null;
                    break;
                }
            }
        }
        internal bool IsDuplicateProfile(Alignment baseAlignment, string profilename, Transaction tr)
        {
            bool result = false;
            // Alignment의 모든 Profile 중 이름이 같은 것 찾기
            foreach (ObjectId profileId in baseAlignment.GetProfileIds())
            {
                Profile profile = tr.GetObject(profileId, OpenMode.ForRead) as Profile;
                if (profile != null && profile.Name == "지반선")
                {
                    result = true;
                    break;
                }
            }
            return result;
        }


    }
}
