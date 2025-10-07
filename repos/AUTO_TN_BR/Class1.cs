using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using System.Text;

namespace AUTO_TN_BR
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize() { }
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
                Alignment baseAlignment = tr.GetObject(baseAlignmentId, OpenMode.ForRead) as Alignment;
                if (baseAlignment == null) return;

                Profile baseProfile = GetProfile(baseAlignment, tr);
                var dem = new AUTODEM();
                dem.BaseAlignment = baseAlignment;
                dem.Step = 40;
                dem.Editor = ed;
                dem.ExtractStations();
                dem.ExtractCoordinates2D();
                dem.ExportTXT();
                dem.ReadElevationsTXT();
                dem.SaveLogToTXT();
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

    }
}
