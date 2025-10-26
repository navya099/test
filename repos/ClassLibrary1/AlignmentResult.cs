using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ClassLibrary1
{
    public readonly record struct OffsetPoint(
    double baseStation,
    double baseEasting,
    double baseNorthing,
    double baseBearing,
    double ElevationBase,
    double targetStation,
    double targetEasting,
    double targetNorthing,
    double targetBearing,
    double ElevationTarget
    );

    public readonly record struct BVEData(
    double Station,
    double OffsetX,
    double OffsetZ,
    double yaw,
    double pitch,
    double roll
    );

    public class AlignmentResult
    {
        public string AlignmentName { get; }
        public List<OffsetPoint> Points { get; } = new();
        public List<BVEData> BVEDatas { get; } = new();

        public List<string> BVELines { get; } = new();
        public List<string> FreeObjLines { get; } = new();

        public AlignmentResult(string name) => AlignmentName = name;

        public void AttachAlignmentHeader()
        {
            BVELines.Add($",;#{AlignmentName}");
            FreeObjLines.Add($",;#{AlignmentName}");

        }

        public void GenerateBVELines(int railindex,int railobjindex)
        {
            int count = BVEDatas.Count;
            for (int i = 0; i < count; i++)
            {
                var p = BVEDatas[i];
                string railKeyword = (i == count - 1) ? "Railend" : "Rail";
                int? index = (i == 0) ? railobjindex : null; // nullable int
                string indexStr = index?.ToString() ?? "";   // null이면 빈 문자열
                BVELines.Add($"{p.Station:F0},.{railKeyword} {railindex};{-p.OffsetX:F3};{p.OffsetZ:F3};{indexStr};");
            }
        }

        public void GenerateFreeObjLines(int railindex, int freeobjindex)
        {
            foreach (var p in BVEDatas)
            {
                FreeObjLines.Add($"{p.Station:F0},.Freeobj {railindex};{freeobjindex};{-p.OffsetX:F3};{p.OffsetZ:F3};{p.yaw};{p.pitch};{p.roll};");
            }
        }
        public IEnumerable<string> ToCsvLines()
        {
            yield return $"#{AlignmentName}";
            foreach (var p in Points)
                yield return $"{p.baseStation:F0},{p.baseEasting:F4},{p.baseNorthing:F4},{p.targetEasting:F4},{p.targetNorthing:F4},{p.ElevationBase:F2},{p.ElevationTarget:F2}";
        }
    }
}