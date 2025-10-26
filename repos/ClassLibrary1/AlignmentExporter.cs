using Autodesk.Civil.DatabaseServices;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ClassLibrary1
{
    public class AlignmentExporter
    {
        public void SavetoFile(IEnumerable<AlignmentResult> results, string folder, bool saveAllAsOneFile)
        {
            Directory.CreateDirectory(folder);
            if (saveAllAsOneFile)
            {
                var allCsv = new List<string> { "baseStation,baseEasting,baseNorthing,baseBearing,ElevationBase,targetStation,targetEasting,targetNorthing,targetBearing,ElevationTarget" };
                var allBve = new List<string>();
                var allFree = new List<string>();


                foreach (var res in results)
                {
                    allCsv.AddRange(res.ToCsvLines());
                    allBve.AddRange(res.BVELines);
                    allFree.AddRange(res.FreeObjLines);
                }
                File.WriteAllLines(Path.Combine(folder, "AllAlignmentOffsets.csv"), allCsv);
                File.WriteAllLines(Path.Combine(folder, "rail.txt"), allBve);
                File.WriteAllLines(Path.Combine(folder, "freeobj.txt"), allFree);

                
                    
                
            }
            else
            {

                // 개별 파일로 저장
                foreach (var res in results)
                {
                    File.WriteAllLines(Path.Combine(folder, $"{res.AlignmentName}.csv"), res.ToCsvLines(), new UTF8Encoding(true));
                    File.WriteAllLines(Path.Combine(folder, $"{res.AlignmentName}.txt"), res.BVELines);
                    File.WriteAllLines(Path.Combine(folder, $"{res.AlignmentName}_freeobj.txt"), res.FreeObjLines);
                }
            }
        }
    }
}
