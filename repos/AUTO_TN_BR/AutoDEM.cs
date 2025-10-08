using Autodesk.Aec.DatabaseServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.Runtime;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

using Exception = Autodesk.AutoCAD.Runtime.Exception;
using ObjectId = Autodesk.AutoCAD.DatabaseServices.ObjectId;

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
        


        

        // -----------------------------
        // 2️⃣ 생성자
        // -----------------------------
        public AUTODEM() 
        {
            Stations = new List<double>();
            Coordinates = new List<Point2d>();
            Coordinates3D = new List<Point3d>();
            Elevations = new List<double>();
            
        }

        // -----------------------------
        // 3️⃣ Alignment 측점 추출
        // -----------------------------
        public void ExtractStations()
        {
            if (BaseAlignment == null)
            {
                Logger.Instance.SetMessage(@"BaseAlignment가 Null입니다. 다시 선택해주세요");
                return;
            }

            Stations.Clear();
            double startStation = BaseAlignment.StartingStation;
            double endStation = BaseAlignment.EndingStation;

            for (double sta = startStation; sta <= endStation; sta += Step)
                Stations.Add(Math.Round(sta, 3));

            if (Stations.Count > 0 && Stations[Stations.Count - 1] < endStation)
                Stations.Add(endStation);

            Logger.Instance.SetMessage($"Stations 추출 성공 {Stations.Count}");
            
        }

        // -----------------------------
        // 4️⃣ 평면 좌표 추출
        // -----------------------------
        public void ExtractCoordinates2D()
        {
            if (BaseAlignment == null || Stations.Count == 0)
            {
                Logger.Instance.SetMessage(@"BaseAlignment또는 Stations가 없습니다. 먼저 ExtractStations()을 실행해주세요");
                
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

            Logger.Instance.SetMessage($"좌표 추출 성공 {Coordinates.Count}"); ;
            
        }

        // -----------------------------
        // 5️⃣ 3D 좌표 추출 (Profile 포함)
        // -----------------------------
        public void ExtractCoordinates3D()
        {
            if (Coordinates.Count == 0)
            {
                Logger.Instance.SetMessage(@"2D Coordinates가 없습니다. 먼저 ExtractCoordinates2D() 호출 필요");
                
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

            Logger.Instance.SetMessage($"총 {Coordinates3D.Count}개의 3D 좌표 생성 완료");
            
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

                Logger.Instance.SetMessage($"CSV 파일 저장 완료: {CSVFilePath}");
                
            }
            catch (Exception ex)
            {
                Logger.Instance.SetMessage($"CSV 저장 실패: {ex.Message}");
                
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
                        //writer.WriteLine(include3D ? "Easting\tNorthing\tElevation" : "Easting\tNorthing");

                    if (include3D)
                    {
                        foreach (var pt in Coordinates3D)
                            writer.WriteLine($"{pt.X:F3},{pt.Y:F3}\t{pt.Z:F3}");
                    }
                    else
                    {
                        foreach (var pt in Coordinates)
                            writer.WriteLine($"{pt.X:F3},{pt.Y:F3}");
                    }
                }

                Logger.Instance.SetMessage($"TXT 파일 저장 완료: {path}");
                
            }
            catch (Exception ex)
            {
                Logger.Instance.SetMessage($"TXT 저장 실패: {ex.Message}");
                
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
                Logger.Instance.SetMessage($"파일이 존재하지 않습니다: {ElevationFilePath}");
                
                return;
            }

            foreach (var line in File.ReadLines(ElevationFilePath))
            {
                if (double.TryParse(line, out double elev))
                    Elevations.Add(elev);
            }

            Logger.Instance.SetMessage($"총 {Elevations.Count}개의 표고값 읽기 완료");
           
        }
  
    }
}
