using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.DatabaseServices;
using Autodesk.AutoCAD.DatabaseServices;

namespace ClassLibrary1
{
    public class PromptHelper
    {

        #region Prompt Methods
        public static string PromptFolderPath(Editor ed)
        {
            var pso = new PromptStringOptions("\nCSV 파일을 저장할 폴더 경로를 입력하세요:");
            pso.AllowSpaces = true;
            pso.DefaultValue = @"c:\temp\eger";

            PromptResult pr = ed.GetString(pso);
            return pr.Status == PromptStatus.OK && !string.IsNullOrWhiteSpace(pr.StringResult) ? pr.StringResult : pso.DefaultValue;
        }

        public static bool PromptSaveOption(Editor ed)
        {
            var pko = new PromptKeywordOptions("\n모든 오프셋 결과를 하나의 CSV 파일로 저장하시겠습니까?");
            pko.Keywords.Add("Yes");
            pko.Keywords.Add("No");
            pko.AllowNone = false;
            return ed.GetKeywords(pko).StringResult == "Yes";
        }

        public static double PromptInterval(Editor ed)
        {
            var pdo = new PromptDoubleOptions("\n계산 측점 간격을 입력하세요:");
            pdo.AllowNegative = false;
            pdo.AllowZero = false;
            return ed.GetDouble(pdo).Value;
        }

        public static int PromptFreeObjIndex(Editor ed)
        {
            var pdf = new PromptDoubleOptions("\n프리오브젝트 인덱스 입력 (기본값: 9):");
            pdf.AllowNegative = false;
            pdf.AllowZero = true;
            pdf.DefaultValue = 9;
            pdf.UseDefaultValue = true;
            return (int)ed.GetDouble(pdf).Value;
        }

        public static int PromptRailObjIndex(Editor ed)
        {
            var pdf = new PromptDoubleOptions("\n레읻인덱스 입력 (기본값: 4):");
            pdf.AllowNegative = false;
            pdf.AllowZero = true;
            pdf.DefaultValue = 4;
            pdf.UseDefaultValue = true;
            return (int)ed.GetDouble(pdf).Value;
        }

        public static ObjectId PromptSelectAlignment(Editor ed)
        {
            var peo = new PromptEntityOptions("\n기준 Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Alignment), true);

            var per = ed.GetEntity(peo);
            return per.Status == PromptStatus.OK ? per.ObjectId : ObjectId.Null;
        }

        public static Profile GetProfile(Alignment alignment, Transaction tr)
        {
            foreach (ObjectId profileId in alignment.GetProfileIds())
            {
                var profile = tr.GetObject(profileId, OpenMode.ForRead) as Profile;
                if (profile != null && profile.ProfileType == ProfileType.FG)
                    return profile;
            }
            return null;
        }
        #endregion
    }
}
