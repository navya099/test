using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Autodesk.Civil.ApplicationServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil.DatabaseServices;
using System.ComponentModel.Design;


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

            // 🗂️ 폴더 경로 입력 받기
            PromptStringOptions pso = new PromptStringOptions("\nCSV 파일을 저장할 폴더 경로를 입력하세요:");
            pso.AllowSpaces = true;
            pso.DefaultValue = @"c:\temp\eger";  // 기본값 설정

            PromptResult pr = ed.GetString(pso);
            string folderPath;

            // 사용자가 입력했는지 체크
            if (pr.Status == PromptStatus.OK && !string.IsNullOrWhiteSpace(pr.StringResult))
            {
                folderPath = pr.StringResult;
            }
            else
            {
                // 입력이 없거나 취소 시 기본값 사용
                folderPath = @"c:\temp\eger";
            }

            // 경로 유효성 검사
            if (!Directory.Exists(folderPath))
            {
                ed.WriteMessage($"\n경로가 유효하지 않습니다: {folderPath} 작업을 중단합니다.");
                return;
            }

            // 📌 통합 저장 여부 확인
            PromptKeywordOptions pko = new PromptKeywordOptions("\n모든 오프셋 결과를 하나의 CSV 파일로 저장하시겠습니까?");
            pko.Keywords.Add("Yes");
            pko.Keywords.Add("No");
            pko.AllowNone = false;
            PromptResult keyRes = ed.GetKeywords(pko);
            bool saveAsOneFile = keyRes.StringResult == "Yes";

            // 📌 측점 계산간격 입력
            PromptDoubleOptions pdo = new PromptDoubleOptions("\n계산 측점 간격을 입력하세요:");
            pdo.AllowNegative = false;
            pdo.AllowZero = false;
            PromptDoubleResult pdr = ed.GetDouble(pdo);
            double interval = pdr.Value;

            // 📌 레일 프리오브젝트 인덱스 입력
            PromptDoubleOptions pdf = new PromptDoubleOptions("\n프리오브젝트 인덱스 입력 (기본값: 9):");
            pdf.AllowNegative = false;
            pdf.AllowZero = true;
            pdf.DefaultValue = 9;
            pdf.UseDefaultValue = true;
            PromptDoubleResult freeidx = ed.GetDouble(pdf);
            int freeobjindex = (int)freeidx.Value;

            // 🎯 기준 Alignment 선택
            PromptEntityOptions peo = new PromptEntityOptions("\n기준 Alignment 객체를 선택하세요:");
            peo.SetRejectMessage("\nAlignment만 선택 가능합니다.");
            peo.AddAllowedClass(typeof(Alignment), true);
            PromptEntityResult per = ed.GetEntity(peo);
            if (per.Status != PromptStatus.OK) return;

            ObjectId baseAlignmentId = per.ObjectId;

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                Alignment baseAlignment = (Alignment)tr.GetObject(baseAlignmentId, OpenMode.ForRead);
                if (baseAlignment == null) return;

                // 베이스선형의 design profile 가져오기
                ObjectIdCollection profileIds = baseAlignment.GetProfileIds();
                Autodesk.Civil.DatabaseServices.Profile baseprofile = null;

                foreach (ObjectId profileId in profileIds)
                {
                    var profile = (Autodesk.Civil.DatabaseServices.Profile)tr.GetObject(profileId, OpenMode.ForRead);
                    if (profile.ProfileType == Autodesk.Civil.DatabaseServices.ProfileType.FG)
                    {
                        baseprofile = profile;
                        break;
                    }
                }

                
                double startStation = baseAlignment.StartingStation;
                double endStation = baseAlignment.EndingStation;

                // BVE 변수
                int railindex = 2;
                int mainrailindx = 0;
                int railobjindex = 4;

                double yaw = 0.0;
                double pitch = 0.0;
                double roll = 0.0;

                List<string> allResults = [];
                List<string> BVETXT = [];
                List<string> BVEFREEOBJ = [];

                allResults.Add("BaseStation,BaseElevation,TargetStation,TargetElevation,OffsetX,OffsetZ");

                foreach (ObjectId targetId in doc.GetAlignmentIds())
                {
                    if (targetId == baseAlignmentId) continue;

                    Alignment targetAlignment = tr.GetObject(targetId, OpenMode.ForRead) as Alignment;
                    if (targetAlignment == null) continue;

                    // 타겟선형의 profile 가져오기
                    ObjectIdCollection targetprofileIds = targetAlignment.GetProfileIds();
                    Autodesk.Civil.DatabaseServices.Profile targetprofile = null;
                    foreach (ObjectId profileId in targetprofileIds)
                    {
                        var profile = (Autodesk.Civil.DatabaseServices.Profile)tr.GetObject(profileId, OpenMode.ForRead);
                        if (profile.ProfileType == Autodesk.Civil.DatabaseServices.ProfileType.FG)
                        {
                            targetprofile = profile;
                            break;
                        }
                    }



                    List<string> resultLines = new List<string>();
                    List<string> bvesyntaxs = new List<string>();
                    List<string> freeobjsyntax = new List<string>();

                    List<(double Sta, double OffsetX, double OffsetY)> validOffsets = [];

                    string line = targetAlignment.Name;
                    resultLines.Add(line);
                    bvesyntaxs.Add($",;{line}\n");
                    freeobjsyntax.Add($",;{line}\n");

                    double adjustedStart = Math.Ceiling(startStation / interval) * interval;
                    for (double sta = adjustedStart; sta <= endStation; sta += interval)
                    {
                        double offsetX = 0.0;
                        double offsetY = 0.0;
                        double targetSta = 0.0;
                        double current_elev = 0.0;
                        double target_elev = 0.0;
                        try
                        {
                            if (baseprofile != null)
                                {
                                current_elev = baseprofile.ElevationAt(sta);

                            }
                            else { 
                                current_elev = 0.0;
                            }
                            
                            baseAlignment.DistanceToAlignment(sta, targetAlignment, ref offsetX, ref targetSta);


                            if (targetprofile != null)
                            {
                                target_elev = targetprofile.ElevationAt(targetSta);
                                offsetY = current_elev - target_elev;
                            }
                            else
                            {
                                target_elev = 0.0;
                                offsetY = 0.0;
                            }

                            string csvLine = $"{sta:F0},{current_elev:F3},{targetSta:F3},{target_elev:F3},{-offsetX:F3},{-offsetY:F3}";
                            resultLines.Add(csvLine);

                            // offset 부호 반전한 채로 저장
                            validOffsets.Add((sta, -offsetX, -offsetY));

                        }
                        catch
                        {
                            // 무시하고 다음으로
                            continue;
                        }

                    }
                    // bvesyntaxs 구성: 마지막 줄만 RailEnd
                    if (validOffsets.Count > 0)
                    {
                        for (int i = 0; i < validOffsets.Count; i++)
                        {
                            var (sta, x, z) = validOffsets[i];
                            // 마지막 점이 아니면 방향 계산
                            if (i < validOffsets.Count - 1)
                            {
                                var (next_sta, x2, z2) = validOffsets[i + 1];
                                double deltaX = x2 - x;
                                double deltaZ = z2 - z;
                                yaw = Math.Atan2(deltaX, interval) * (180.0 / Math.PI);     // 가로 방향 각도
                                pitch = Math.Atan2(deltaZ, interval) * (180.0 / Math.PI);   // 세로 방향 각도
                            }


                            if (i == validOffsets.Count - 1)
                            {
                                bvesyntaxs.Add($"{sta:F0},.RailEnd {railindex};{x:F3};{z:F3};{railobjindex};");
                            }
                            else
                            {
                                if ((int)sta % 25 == 0)// sta가 25의 배수일 때만 실행
                                {
                                    bvesyntaxs.Add($"{sta:F0},.Rail {railindex};{x:F3};{z:F3};{railobjindex};");
                                }
                                if ((int)sta % 5 == 0)// sta가 5의 배수일 때만 실행
                                {
                                    freeobjsyntax.Add($"{sta:F0},.Freeobj 0;{freeobjindex};{x:F3};{z:F3};{yaw};{pitch};{roll};");
                                }
                            }
                        }
                    }
                    if (saveAsOneFile)
                    {
                        allResults.AddRange(resultLines);
                        BVETXT.AddRange(bvesyntaxs);
                        BVEFREEOBJ.AddRange(freeobjsyntax);
                    }
                    else
                    {
                        string csvPath = Path.Combine(folderPath, $"{targetAlignment.Name}.csv");
                        File.WriteAllLines(csvPath, new[] { "BaseStation,BaseElevation,TargetStation,TargetElevation,OffsetX,OffsetZ" }.Concat(resultLines));
                        ed.WriteMessage($"\n{csvPath} 저장 완료.");

                        //bve문법 저장
                        string txtPath = Path.Combine(folderPath, $"{targetAlignment.Name}.txt");
                        File.WriteAllLines(txtPath, bvesyntaxs);
                    }
                    railindex++;
                }

                if (saveAsOneFile)
                {
                    string combinedcsvPath = Path.Combine(folderPath, "AllAlignmentOffsets.csv");
                    File.WriteAllLines(combinedcsvPath, allResults);
                    ed.WriteMessage($"\n모든 데이터가 {combinedcsvPath} 에 저장되었습니다.");

                    string combinedtxtPath = Path.Combine(folderPath, "rail.txt");
                    File.WriteAllLines(combinedtxtPath, BVETXT); // Rail 문법

                    string combinedfreeobjPath = Path.Combine(folderPath, "freeobj.txt");
                    File.WriteAllLines(combinedfreeobjPath, BVEFREEOBJ); // Freeobj 문법
                }


                tr.Commit();
            }
        }
    }
}
