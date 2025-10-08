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
        
        
        public List<double> Stations { get; private set; }   // 측점 리스트
        public List<Point2d> Coordinates { get; private set; } // 평면 좌표
        public List<Point3d> Coordinates3D { get; private set; } // 3D 좌표
        public List<double> Elevations { get; private set; } // 외부 표고(TXT/TIN)

        public string CSVFilePath { get; set; } = @"C:\temp\Coordinates.csv";

        public string TXTFilePath { get; set; } = @"C:\temp\Coordinates.txt";
        public string ElevationFilePath { get; set; } = @"C:\temp\elevation.txt";

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
        // 3⃣ 메서드
        // -----------------------------

        /// <summary>
        /// dem처리 및 선형 좌표출력 수행 메소드
        /// </summary>
        public void ProcessDEM(Alignment baseAlignment)
        {
            //인스턴스생성
            var demProcessor = new DEMProcessor();
            var alignmentProvider = new AlignmentService
            {
                BaseAlignment = baseAlignment
            };

            //좌표추출
            alignmentProvider.ExtractStations(40);
            alignmentProvider.ExtractCoordinates2D(0.0);

            //좌표txt저장
            _ = FileService.Export(TXTFilePath, false, alignmentProvider.Coordinates);

            //python dem 처리 스크립트 실행
            bool result = demProcessor.RunPythonScript();
            if (!result) throw new System.Exception("파이썬 스크립트 실행 실패");
            
            //표고 불러오기(double 형식으로 캐스팅)
            List<double> elevations = Utils.StringToDoubleList(FileService.ImportLines(ElevationFilePath, true));

            //속성 저장
            Stations = alignmentProvider.Stations;
            Coordinates = alignmentProvider.Coordinates;
            Elevations = elevations;
        }
    }
}
