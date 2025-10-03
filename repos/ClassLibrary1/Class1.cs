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

            string folderPath = PromptFolderPath(ed);
            if (string.IsNullOrEmpty(folderPath) || !Directory.Exists(folderPath))
            {
                ed.WriteMessage($"\n경로가 유효하지 않습니다: {folderPath}");
                return;
            }

            bool saveAsOneFile = PromptSaveOption(ed);
            double interval = PromptInterval(ed);
            int freeobjIndex = PromptFreeObjIndex(ed);

            ObjectId baseAlignmentId = PromptSelectAlignment(ed);
            if (baseAlignmentId.IsNull) return;

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                Alignment baseAlignment = tr.GetObject(baseAlignmentId, OpenMode.ForRead) as Alignment;
                if (baseAlignment == null) return;

                Profile baseProfile = GetProfile(baseAlignment, tr);

                AlignmentProcessor processor = new AlignmentProcessor(baseAlignment, baseProfile, interval, freeobjIndex);
                processor.ProcessAllAlignments(doc, tr, folderPath, saveAsOneFile);

                tr.Commit();
            }
        }

        #region Prompt Methods
        private string PromptFolderPath(Editor ed)
        {
            var pso = new PromptStringOptions("\nCSV 파일을 저장할 폴더 경로를 입력하세요:");
            pso.AllowSpaces = true;
            pso.DefaultValue = @"c:\temp\eger";

            PromptResult pr = ed.GetString(pso);
            return pr.Status == PromptStatus.OK && !string.IsNullOrWhiteSpace(pr.StringResult) ? pr.StringResult : pso.DefaultValue;
        }

        private bool PromptSaveOption(Editor ed)
        {
            var pko = new PromptKeywordOptions("\n모든 오프셋 결과를 하나의 CSV 파일로 저장하시겠습니까?");
            pko.Keywords.Add("Yes");
            pko.Keywords.Add("No");
            pko.AllowNone = false;
            return ed.GetKeywords(pko).StringResult == "Yes";
        }

        private double PromptInterval(Editor ed)
        {
            var pdo = new PromptDoubleOptions("\n계산 측점 간격을 입력하세요:");
            pdo.AllowNegative = false;
            pdo.AllowZero = false;
            return ed.GetDouble(pdo).Value;
        }

        private int PromptFreeObjIndex(Editor ed)
        {
            var pdf = new PromptDoubleOptions("\n프리오브젝트 인덱스 입력 (기본값: 9):");
            pdf.AllowNegative = false;
            pdf.AllowZero = true;
            pdf.DefaultValue = 9;
            pdf.UseDefaultValue = true;
            return (int)ed.GetDouble(pdf).Value;
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
        #endregion
    }

    #region Alignment Processing Class
    public class AlignmentProcessor
    {
        private Alignment BaseAlignment { get; }
        private Profile BaseProfile { get; }
        private double Interval { get; }
        private int FreeObjIndex { get; }

        private int RailIndex = 2;
        private int RailObjIndex = 4;

        public AlignmentProcessor(Alignment baseAlignment, Profile baseProfile, double interval, int freeObjIndex)
        {
            BaseAlignment = baseAlignment;
            BaseProfile = baseProfile;
            Interval = interval;
            FreeObjIndex = freeObjIndex;
        }

        public void ProcessAllAlignments(CivilDocument doc, Transaction tr, string folderPath, bool saveAsOneFile)
        {
            List<string> allResults = new List<string> { "BaseStation,BaseElevation,TargetStation,TargetElevation,OffsetX,OffsetZ" };
            List<string> BVEtxt = new List<string>();
            List<string> BVEfreeObj = new List<string>();

            double startStation = BaseAlignment.StartingStation;
            double endStation = BaseAlignment.EndingStation;

            foreach (ObjectId targetId in doc.GetAlignmentIds())
            {
                if (targetId == BaseAlignment.ObjectId) continue;

                Alignment targetAlignment = tr.GetObject(targetId, OpenMode.ForRead) as Alignment;
                if (targetAlignment == null) continue;

                Profile targetProfile = GetProfile(targetAlignment, tr);

                AlignmentResult result = ProcessAlignment(targetAlignment, targetProfile, startStation, endStation);

                if (saveAsOneFile)
                {
                    allResults.AddRange(result.CSVLines);
                    BVEtxt.AddRange(result.BVELines);
                    BVEfreeObj.AddRange(result.FreeObjLines);
                }
                else
                {
                    File.WriteAllLines(Path.Combine(folderPath, $"{targetAlignment.Name}.csv"),
                        new[] { "BaseStation,BaseElevation,TargetStation,TargetElevation,OffsetX,OffsetZ" }.Concat(result.CSVLines));
                    File.WriteAllLines(Path.Combine(folderPath, $"{targetAlignment.Name}.txt"), result.BVELines);
                }

                RailIndex++;
            }

            if (saveAsOneFile)
            {
                File.WriteAllLines(Path.Combine(folderPath, "AllAlignmentOffsets.csv"), allResults);
                File.WriteAllLines(Path.Combine(folderPath, "rail.txt"), BVEtxt);
                File.WriteAllLines(Path.Combine(folderPath, "freeobj.txt"), BVEfreeObj);
            }
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

        private AlignmentResult ProcessAlignment(Alignment targetAlignment, Profile targetProfile, double startStation, double endStation)
        {
            var result = new AlignmentResult();

            double adjustedStart = Math.Ceiling(startStation / Interval) * Interval;
            for (double sta = adjustedStart; sta <= endStation; sta += Interval)
            {
                double offsetX = 0.0;
                double offsetY = 0.0;
                double targetSta = 0.0;
                double currentElev = BaseProfile?.ElevationAt(sta) ?? 0.0;
                double targetElev = 0.0;

                try
                {
                    BaseAlignment.DistanceToAlignment(sta, targetAlignment, ref offsetX, ref targetSta);

                    if (targetProfile != null)
                    {
                        targetElev = targetProfile.ElevationAt(targetSta);
                        offsetY = currentElev - targetElev;
                    }

                    string csvLine = $"{sta:F0},{currentElev:F3},{targetSta:F3},{targetElev:F3},{-offsetX:F3},{-offsetY:F3}";
                    result.CSVLines.Add(csvLine);
                    result.Offsets.Add((sta, -offsetX, -offsetY));
                }
                catch
                {
                    continue;
                }
            }

            // BVE Rail/Freeobj 문법 생성
            result.GenerateBVELines(ref RailIndex, RailObjIndex, FreeObjIndex, Interval);
            return result;
        }
    }

    #endregion

    #region Alignment Result Class
    public class AlignmentResult
    {
        public List<string> CSVLines { get; } = new List<string>();
        public List<string> BVELines { get; } = new List<string>();
        public List<string> FreeObjLines { get; } = new List<string>();
        public List<(double Sta, double X, double Z)> Offsets { get; } = new List<(double, double, double)>();

        public void GenerateBVELines(ref int railIndex, int railObjIndex, int freeObjIndex, double interval)
        {
            double yaw = 0.0;
            double pitch = 0.0;
            double roll = 0.0;

            for (int i = 0; i < Offsets.Count; i++)
            {
                var (sta, x, z) = Offsets[i];

                if (i < Offsets.Count - 1)
                {
                    var (nextSta, x2, z2) = Offsets[i + 1];
                    double deltaX = x2 - x;
                    double deltaZ = z2 - z;
                    yaw = Math.Atan2(deltaX, interval) * (180.0 / Math.PI);
                    pitch = Math.Atan2(deltaZ, interval) * (180.0 / Math.PI);
                }

                if (i == Offsets.Count - 1)
                {
                    BVELines.Add($"{sta:F0},.RailEnd {railIndex};{x:F3};{z:F3};{railObjIndex};");
                }
                else
                {
                    if ((int)sta % 25 == 0)
                        BVELines.Add($"{sta:F0},.Rail {railIndex};{x:F3};{z:F3};{railObjIndex};");
                    if ((int)sta % 5 == 0)
                        FreeObjLines.Add($"{sta:F0},.Freeobj 0;{freeObjIndex};{x:F3};{z:F3};{yaw};{pitch};{roll};");
                }
            }
        }
    }
    #endregion
}
