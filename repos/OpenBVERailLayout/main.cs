using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Autodesk.Civil.ApplicationServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.DatabaseServices;
using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;

namespace OpenBVERailLayout
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize() { }

        public void Terminate() { }

        [CommandMethod("ExtractOpenBVERailLayout")]
        public void ExtractOpenBVERailLayout()
        {
            Editor ed = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            CivilDocument doc = CivilApplication.ActiveDocument;
            Database db = CoreApp.DocumentManager.MdiActiveDocument.Database;

            // 🗂️ 폴더 경로 입력 받기
            PromptStringOptions pso = new PromptStringOptions("\nCSV 파일을 저장할 폴더 경로를 입력하세요:");
            pso.AllowSpaces = true;
            pso.DefaultValue = @"c:\temp\eger";  // 기본값 설정

            PromptResult pr = ed.GetString(pso);
            string folderPath = (pr.Status == PromptStatus.OK && !string.IsNullOrWhiteSpace(pr.StringResult))
                ? pr.StringResult
                : @"c:\temp\eger";

            // 경로 유효성 검사 및 자동 생성
            if (!Directory.Exists(folderPath))
            {
                try { Directory.CreateDirectory(folderPath); }
                catch { ed.WriteMessage($"\n경로 생성 실패: {folderPath} 작업을 중단합니다."); return; }
            }

            // 📌 측점 계산간격 입력 (예: 5m 고정 절대 격자)
            PromptDoubleOptions pdo = new PromptDoubleOptions("\n계산 측점 간격을 입력하세요 (기본 25m 또는 5m 정밀):");
            pdo.AllowNegative = false;
            pdo.AllowZero = false;
            pdo.DefaultValue = 5.0;
            pdo.UseDefaultValue = true;
            PromptDoubleResult pdr = ed.GetDouble(pdo);
            if (pdr.Status != PromptStatus.OK) return;
            double interval = pdr.Value;

            // 🎯 기준 자선(Base Alignment) 선택 - 변환 연산 가이드라인용 데이터 확보용
            PromptEntityOptions peo = new PromptEntityOptions("\n기준(자선) Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Autodesk.Civil.DatabaseServices.Alignment), true);
            PromptEntityResult per = ed.GetEntity(peo);
            if (per.Status != PromptStatus.OK) return;

            ObjectId baseAlignmentId = per.ObjectId;

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                var baseAlignment = (Autodesk.Civil.DatabaseServices.Alignment)tr.GetObject(baseAlignmentId, OpenMode.ForRead);
                if (baseAlignment == null) return;

                // 1. 자선(Base) 고유의 절대좌표 데이터 먼저 추출 및 저장
                List<string> baseLines = ["Station,Easting,Northing,Elevation,Bearing"];
                double baseStart = baseAlignment.StartingStation;
                double baseEnd = baseAlignment.EndingStation;
                double adjustedBaseStart = Math.Ceiling(baseStart / interval) * interval;

                // 자선 프로파일 로드
                Autodesk.Civil.DatabaseServices.Profile baseProfile = null;
                foreach (ObjectId pId in baseAlignment.GetProfileIds())
                {
                    var prof = (Autodesk.Civil.DatabaseServices.Profile)tr.GetObject(pId, OpenMode.ForRead);
                    if (prof.ProfileType == ProfileType.FG || prof.ProfileType == ProfileType.OffsetProfile)
                    {
                        baseProfile = prof;
                        break;
                    }
                }

                for (double sta = adjustedBaseStart; sta <= baseEnd; sta += interval)
                {
                    double e = 0.0, n = 0.0, br = 0.0;
                    try
                    {
                        baseAlignment.PointLocation(sta, 0.0,0.001, ref e, ref n, ref br);
                        double elev = baseProfile?.ElevationAt(sta) ?? 0.0;
                        baseLines.Add($"{sta:F2},{e:F4},{n:F4},{elev:F4},{br:F6}");
                    }
                    catch { continue; }
                }
                // 자선 종점 강제 추가 (결친구간 마감용 데이터)
                try
                {
                    double e = 0.0, n = 0.0, br = 0.0;
                    baseAlignment.PointLocation(baseEnd, 0.0, 0.001, ref e, ref n, ref br);
                    double elev = baseProfile?.ElevationAt(baseEnd) ?? 0.0;
                    baseLines.Add($"{baseEnd:F2},{e:F4},{n:F4},{elev:F4},{br:F6}");
                }
                catch { }

                File.WriteAllLines(Path.Combine(folderPath, "Base_Alignment_Absolute.csv"), baseLines);

                // 2. 모든 타겟 선형(타선)들을 돌며 순수 절대좌표 클라우드 추출
                foreach (ObjectId targetId in doc.GetAlignmentIds())
                {
                    var targetAlignment = tr.GetObject(targetId, OpenMode.ForRead) as Autodesk.Civil.DatabaseServices.Alignment;
                    if (targetAlignment == null) continue;

                    // 파일 이름 안전 문자 처리
                    string safeName = string.Concat(targetAlignment.Name.Split(Path.GetInvalidFileNameChars()));
                    List<string> targetLines = ["Station,Easting,Northing,Elevation,Bearing"];

                    // 타겟 고유의 시종점 격자 계산
                    double tStart = targetAlignment.StartingStation;
                    double tEnd = targetAlignment.EndingStation;
                    double adjustedTStart = Math.Ceiling(tStart / interval) * interval;

                    // 타겟 프로파일 로드
                    Autodesk.Civil.DatabaseServices.Profile targetProfile = null;
                    foreach (ObjectId profileId in targetAlignment.GetProfileIds())
                    {
                        var prof = (Autodesk.Civil.DatabaseServices.Profile)tr.GetObject(profileId, OpenMode.ForRead);
                        if (prof.ProfileType == ProfileType.FG || prof.ProfileType == ProfileType.OffsetProfile)
                        {
                            targetProfile = prof;
                            break;
                        }
                    }

                    // 타선 내부 절대 격자 루프
                    for (double sta = adjustedTStart; sta <= tEnd; sta += interval)
                    {
                        double x_coord = 0.0;
                        double y_coord = 0.0;
                        double bearing = 0.0;
                        double target_elev = 0.0;

                        try
                        {
                            target_elev = targetProfile != null ? targetProfile.ElevationAt(sta) : 0.0;
                            // API 오버로드 일치시킴 (sta, offset, ref E, ref N, ref Bearing)
                            targetAlignment.PointLocation(sta, 0.0, 0.001, ref x_coord, ref y_coord, ref bearing);

                            targetLines.Add($"{sta:F2},{x_coord:F4},{y_coord:F4},{target_elev:F4},{bearing:F6}");
                        }
                        catch { continue; }
                    }

                    // 🌟 [핵심 해결] 98.27m 같은 단점 결친구간의 공백을 막기 위해 '실제 종점' 강제 추가
                    try
                    {
                        double x_coord = 0.0, y_coord = 0.0, bearing = 0.0;
                        double target_elev = targetProfile != null ? targetProfile.ElevationAt(tEnd) : 0.0;
                        targetAlignment.PointLocation(tEnd, 0.0,0.001,  ref x_coord, ref y_coord, ref bearing);

                        targetLines.Add($"{tEnd:F2},{x_coord:F4},{y_coord:F4},{target_elev:F4},{bearing:F6}");
                    }
                    catch { }

                    // 각 타선별 독립 절대좌표 파일 내보내기
                    string csvPath = Path.Combine(folderPath, $"{safeName}_Absolute.csv");
                    File.WriteAllLines(csvPath, targetLines);
                }

                tr.Commit();
                ed.WriteMessage($"\n[SUCCESS] 모든 선형의 100% 절대좌표 데이터가 {folderPath}에 내보내졌습니다.");
            }
        }
    }
}