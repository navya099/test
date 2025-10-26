using Autodesk.Civil.DatabaseServices;
using System;
using Autodesk.AutoCAD.Geometry;
using System.Reflection.Metadata.Ecma335;

namespace ClassLibrary1
{
    public class AlignmentCalculator
    {
        public AlignmentResult ComputeOffsetForAlignment(
            Alignment baseAlignment,
            Profile baseProfile,
            Alignment targetAlignment,
            Profile targetProfile,
            double interval)
        {
            var result = new AlignmentResult(targetAlignment.Name);
            double startStation = baseAlignment.StartingStation;
            double endStation = baseAlignment.EndingStation;
            double adjustedStart = Math.Ceiling(startStation / interval) * interval;

            try
            {
                for (double sta = adjustedStart; sta <= endStation; sta += interval)
                {
                    try
                    {
                        // Elevation 계산
                        double currentElev = baseProfile?.ElevationAt(sta) ?? 0.0;
                        double nextElev = (sta + interval <= endStation) ? baseProfile?.ElevationAt(sta + interval) ?? currentElev : currentElev;

                        // Offset 및 targetStation 계산
                        double offsetX = 0.0;
                        double offsetY = 0.0;
                        double targetSta = 0.0;
                        baseAlignment.DistanceToAlignment(sta, targetAlignment, ref offsetX, ref targetSta);

                        // 현재 및 타겟 Alignment 좌표와 방위
                        double stationEasting = 0.0, stationNorthing = 0.0, stationBearing = 0.0;
                        baseAlignment.PointLocation(sta, 0.0, 0.001, ref stationEasting, ref stationNorthing, ref stationBearing);

                        double targetEasting = 0.0, targetNorthing = 0.0, targetBearing = 0.0;
                        targetAlignment.PointLocation(targetSta, 0.0, 0.001, ref targetEasting, ref targetNorthing, ref targetBearing);

                        // Yaw & Pitch 계산
                        double yaw = stationBearing - targetBearing;
                        double deltaZ = nextElev - currentElev;
                        double pitch = Math.Atan2(deltaZ, interval) * (180.0 / Math.PI);
                        double roll = 0.0;
                        // Target Elevation이 있으면 offsetY 계산
                        double targetElev = 0.0;
                        if (targetProfile != null)
                        {
                            targetElev = targetProfile.ElevationAt(targetSta);
                            offsetY = currentElev - targetElev;
                        }

                        // 결과 객체에 추가
                        result.Points.Add(new OffsetPoint(sta, stationEasting, stationNorthing, stationBearing, currentElev, targetSta, targetEasting, targetNorthing, targetBearing, targetElev));
                        result.BVEDatas.Add(new BVEData(sta, offsetX, offsetY, yaw, pitch, roll));   
                    }
                    catch
                    {
                        //pointnotempty예외시 계속해야함
                        continue;
                    }
                }
            }
            catch (Exception ex)
            {
                //심각한 예외(선형에 접근 불가 등)
                Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument.Editor
                    .WriteMessage($"\n[WARN] {targetAlignment.Name}: {ex.Message}");
            }
            return result;
        }
    }
}
