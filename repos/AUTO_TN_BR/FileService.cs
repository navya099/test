using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Autodesk.AutoCAD.Geometry;

namespace AUTO_TN_BR
{
    internal static class FileService
    {
        /// <summary>
        /// Point2d / Point3d 데이터를 CSV나 TXT로 저장
        /// </summary>
        /// <typeparam name="T">Point2d 또는 Point3d</typeparam>
        /// <param name="path">저장 경로</param>
        /// <param name="includeHeader">헤더 포함 여부</param>
        /// <param name="data">좌표 리스트</param>
        /// <param name="delimiter">기본 ',' (CSV), '\t' (TXT)</param>
        /// <returns>저장 성공 여부</returns>
        public static bool Export<T>(string path, bool includeHeader, List<T> data, string delimiter = ",")
        {
            try
            {
                var dir = Path.GetDirectoryName(path);
                if (!string.IsNullOrEmpty(dir))
                    Directory.CreateDirectory(dir);

                using var writer = new StreamWriter(path, false, Encoding.UTF8);

                // 헤더 작성
                if (includeHeader)
                {
                    if (typeof(T) == typeof(Point3d))
                        writer.WriteLine($"Easting{delimiter}Northing{delimiter}Elevation");
                    else if (typeof(T) == typeof(Point2d))
                        writer.WriteLine($"Easting{delimiter}Northing");
                }

                // 본문 작성
                foreach (var item in data)
                {
                    if (item is Point3d p3)
                        writer.WriteLine($"{p3.X:F3}{delimiter}{p3.Y:F3}{delimiter}{p3.Z:F3}");
                    else if (item is Point2d p2)
                        writer.WriteLine($"{p2.X:F3}{delimiter}{p2.Y:F3}");
                }

                Logger.Instance.SetMessage($"파일 저장 완료: {path}");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Instance.SetMessage($"파일 저장 실패: {ex.Message}");
                return false;
            }
        }
        /// <summary>
        /// TXT 파일을 라인 단위로 읽어 문자열 리스트로 반환
        /// </summary>
        public static List<string> ImportLines(string filePath, bool skipEmptyLines = true)
        {
            var result = new List<string>();

            try
            {
                if (!File.Exists(filePath))
                {
                    Logger.Instance.SetMessage($"파일이 존재하지 않습니다: {filePath}");
                    return result;
                }

                foreach (var line in File.ReadLines(filePath))
                {
                    if (skipEmptyLines && string.IsNullOrWhiteSpace(line))
                        continue;

                    result.Add(line.Trim());
                }

                Logger.Instance.SetMessage($"총 {result.Count}개의 라인 읽기 완료: {filePath}");
            }
            catch (Exception ex)
            {
                Logger.Instance.SetMessage($"파일 읽기 실패: {ex.Message}");
            }

            return result;
        }
    }
}
