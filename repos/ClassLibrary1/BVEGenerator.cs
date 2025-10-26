using Autodesk.AutoCAD.DatabaseServices.Filters;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace ClassLibrary1
{
    public static class BVEGenerator
    {
        public static IEnumerable<string> GenerateBVELines(AlignmentResult result, int index)
        {
            yield return $";,;#{result.AlignmentName}";
            foreach (var p in result.BVEDatas)
            {
                yield return $"{p.Station:F0},.Rail {index};{p.OffsetX:F3};{p.OffsetZ:F3};";
                index++;
            }
        }

        public static IEnumerable<string> GenerateFreeObjLines(AlignmentResult result, int index)
        {
            yield return $",;#{result.AlignmentName}";
            foreach (var p in result.BVEDatas)
            {
                yield return $"{p.Station:F0},.Freeobj {index};{p.OffsetX:F3};{p.OffsetZ:F3}"; // 필요한 데이터 계산
                index++;
            }
        }

    }

}
