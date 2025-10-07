using System;
using System.Collections.Generic;
using System.IO;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;
using Autodesk.Civil.DatabaseServices;

namespace AUTO_TN_BR
{
    public class AUTODEM
    {
        // -----------------------------
        // 1️⃣ 속성
        // -----------------------------
        public Alignment BaseAlignment { get; set; }         // 기준 Alignment
        public Profile BaseProfile { get; set; }             // FG Profile
        public List<double> Stations { get; private set; }   // 측점 리스트
        public List<Point2d> Coordinates { get; private set; } // 평면 좌표
        public List<Point3d> Coordinates3D { get; private set; } // 3D 좌표
        public List<double> Elevations { get; private set; } // 외부 표고(TXT/TIN)
        
        public double Step { get; set; } = 10.0;             // 측점 간격
        public double Offset { get; set; } = 0.0;            // Alignment 오프셋
        public string CSVFilePath { get; set; } = @"C:\temp\Coordinates.csv";
        public string ElevationFilePath { get; set; } = @"C:\temp\elevation.txt";
        public bool IncludeHeader { get; set; } = true;      // CSV 헤더 포함 여부
        public string LastMessage { get; private set; }      // 처리 상태 메시지

        public List<string> LogMessages { get; private set; }  // 메시지 로그


        public Editor Editor { get; set; }  // AutoCAD 명령창 출력용

        // -----------------------------
        // 2️⃣ 생성자
        // -----------------------------
        public AUTODEM() 
        {
            Stations = new List<double>();
            Coordinates = new List<Point2d>();
            Coordinates3D = new List<Point3d>();
            Elevations = new List<double>();
            LogMessages = new List<string>();
        }

        // -----------------------------
        // 3️⃣ Alignment 측점 추출
        // -----------------------------
        public void ExtractStations()
        {
            if (BaseAlignment == null)
            {
                LastMessage = "BaseAlignment가 설정되지 않았습니다.";
                SetMessage(LastMessage);
                return;
            }

            Stations.Clear();
            double startStation = BaseAlignment.StartingStation;
            double endStation = BaseAlignment.EndingStation;

            for (double sta = startStation; sta <= endStation; sta += Step)
                Stations.Add(Math.Round(sta, 3));

            if (Stations.Count > 0 && Stations[Stations.Count - 1] < endStation)
                Stations.Add(endStation);

            LastMessage = $"총 {Stations.Count}개의 측점 생성 완료";
            SetMessage(LastMessage);
        }

        // -----------------------------
        // 4️⃣ 평면 좌표 추출
        // -----------------------------
        public void ExtractCoordinates2D()
        {
            if (BaseAlignment == null || Stations.Count == 0)
            {
                LastMessage = "BaseAlignment 또는 Stations가 없습니다.";
                SetMessage(LastMessage);
                return;
            }

            Coordinates.Clear();
            double easting = 0.0, northing = 0.0;

            foreach (var sta in Stations)
            {
                try
                {
                    BaseAlignment.PointLocation(sta, Offset, ref easting, ref northing);
                    Coordinates.Add(new Point2d(easting, northing));
                }
                catch (Autodesk.Civil.PointNotOnEntityException)
                {
                    continue;
                }
            }

            LastMessage = $"총 {Coordinates.Count}개의 평면 좌표 추출 완료";
            SetMessage(LastMessage);
        }

        // -----------------------------
        // 5️⃣ 3D 좌표 추출 (Profile 포함)
        // -----------------------------
        public void ExtractCoordinates3D()
        {
            if (Coordinates.Count == 0)
            {
                LastMessage = "2D Coordinates가 없습니다. 먼저 ExtractCoordinates2D() 호출 필요";
                SetMessage(LastMessage);
                return;
            }

            Coordinates3D.Clear();

            foreach (var sta in Stations)
            {
                try
                {
                    double easting = 0.0, northing = 0.0;
                    BaseAlignment.PointLocation(sta, Offset, ref easting, ref northing);

                    double elev = BaseProfile != null ? BaseProfile.ElevationAt(sta) : 0.0;
                    Coordinates3D.Add(new Point3d(easting, northing, elev));
                }
                catch
                {
                    continue;
                }
            }

            LastMessage = $"총 {Coordinates3D.Count}개의 3D 좌표 생성 완료";
            SetMessage(LastMessage);
        }

        // -----------------------------
        // 6️⃣ CSV로 출력 (2D or 3D)
        // -----------------------------
        public void ExportCSV(bool include3D = false)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(CSVFilePath));

                using (StreamWriter writer = new StreamWriter(CSVFilePath, false, System.Text.Encoding.UTF8))
                {
                    if (IncludeHeader)
                        writer.WriteLine(include3D ? "Easting,Northing,Elevation" : "Easting,Northing");

                    if (include3D)
                    {
                        foreach (var pt in Coordinates3D)
                            writer.WriteLine($"{pt.X:F3},{pt.Y:F3},{pt.Z:F3}");
                    }
                    else
                    {
                        foreach (var pt in Coordinates)
                            writer.WriteLine($"{pt.X:F3},{pt.Y:F3}");
                    }
                }

                LastMessage = $"CSV 파일 저장 완료: {CSVFilePath}";
                SetMessage(LastMessage);
            }
            catch (Exception ex)
            {
                LastMessage = $"CSV 저장 실패: {ex.Message}";
                SetMessage(LastMessage);
            }
        }

        // -----------------------------
        // 6️⃣ txt로 출력 (2D or 3D)
        // -----------------------------
        public void ExportTXT(bool include3D = false, string txtFilePath = null)
        {
            try
            {
                // 파일 경로 지정: 인수 없으면 기본 경로 사용
                string path = txtFilePath ?? @"C:\temp\Coordinates.txt";
                Directory.CreateDirectory(Path.GetDirectoryName(path));

                using (StreamWriter writer = new StreamWriter(path, false, System.Text.Encoding.UTF8))
                {
                    if (IncludeHeader)
                        writer.WriteLine(include3D ? "Easting\tNorthing\tElevation" : "Easting\tNorthing");

                    if (include3D)
                    {
                        foreach (var pt in Coordinates3D)
                            writer.WriteLine($"{pt.X:F3}\t{pt.Y:F3}\t{pt.Z:F3}");
                    }
                    else
                    {
                        foreach (var pt in Coordinates)
                            writer.WriteLine($"{pt.X:F3}\t{pt.Y:F3}");
                    }
                }

                LastMessage = $"TXT 파일 저장 완료: {path}";
                SetMessage(LastMessage);
            }
            catch (Exception ex)
            {
                LastMessage = $"TXT 저장 실패: {ex.Message}";
                SetMessage(LastMessage);
            }
        }


        // -----------------------------
        // 7️⃣ TXT에서 표고 읽기
        // -----------------------------
        public void ReadElevationsTXT()
        {
            Elevations.Clear();

            if (!File.Exists(ElevationFilePath))
            {
                LastMessage = $"파일이 존재하지 않습니다: {ElevationFilePath}";
                SetMessage(LastMessage);
                return;
            }

            foreach (var line in File.ReadLines(ElevationFilePath))
            {
                if (double.TryParse(line, out double elev))
                    Elevations.Add(elev);
            }

            LastMessage = $"총 {Elevations.Count}개의 표고값 읽기 완료";
            SetMessage(LastMessage);
        }

        private void SetMessage(string msg)
        {
            LastMessage = msg;
            LogMessages.Add(msg);                  // 로그 누적
            Editor?.WriteMessage("\n" + msg); // Editor가 null이 아니면 출력
        }

        public void SaveLogToTXT(string logFilePath = @"C:\temp\AUTODEM_Log.txt")
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(logFilePath));
                File.WriteAllLines(logFilePath, LogMessages);
                SetMessage($"로그 파일 저장 완료: {logFilePath}");
            }
            catch (Exception ex)
            {
                SetMessage($"로그 저장 실패: {ex.Message}");
            }
        }

    }
}
