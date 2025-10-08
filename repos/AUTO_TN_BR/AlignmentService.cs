using Autodesk.AutoCAD.Geometry;
using Autodesk.Civil.DatabaseServices;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AUTO_TN_BR
{
    internal class AlignmentService
    {
        /// <summary>
        /// 기준 Alignment
        /// </summary>
        public Alignment BaseAlignment { get; set; }
        /// <summary>
        /// 측점 리스트
        /// </summary>
        public List<double> Stations { get; private set; }
        /// <summary>
        /// 평면 좌표
        /// </summary>
        public List<Point2d> Coordinates { get; private set; }
        /// <summary>
        /// 3D 좌표
        /// </summary>
        public List<Point3d> Coordinates3D { get; private set; } 

        public AlignmentService() {
            Stations = new List<double>();
            Coordinates = new List<Point2d>();
            Coordinates3D = new List<Point3d>();
        }

        // -----------------------------
        // 3️⃣ Alignment 측점 추출
        // -----------------------------
        public void ExtractStations(double Step)
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
        public void ExtractCoordinates2D(double Offset)
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


        
    }
}
