using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AUTO_TN_BR
{
    internal static class Utils
    {
        /// <summary>
        /// 문자열 리스트를 double 리스트로 변환
        /// </summary>
        /// <param name="stringList">변환할 문자열 리스트</param>
        /// <param name="ignoreInvalid">잘못된 형식 무시 여부 (기본 true)</param>
        /// <returns>double 리스트</returns>
        public static List<double> StringToDoubleList(List<string> stringList, bool ignoreInvalid = true)
        {
            var result = new List<double>();

            foreach (var s in stringList)
            {
                if (double.TryParse(s, out double value))
                {
                    result.Add(value);
                }
                else if (!ignoreInvalid)
                {
                    throw new FormatException($"'{s}'를 double로 변환할 수 없습니다.");
                }
            }

            return result;
        }
    }
}
