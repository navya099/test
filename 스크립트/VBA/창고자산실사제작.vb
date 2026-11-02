
Option Explicit

Sub 창고_자산실사_양식자동생성()

    Const MAX_ITEMS As Long = 23

    Dim wbSrc As Workbook
    Dim wbForm As Workbook
    Dim wbOut As Workbook

    Dim wsSrc As Worksheet
    Dim wsTemplate As Worksheet
    Dim wsNew As Worksheet

    Dim basePath As String
    Dim srcPath As String
    Dim formPath As String
    Dim outPath As String

    Dim depts As Variant
    Dim dept As Variant
    Dim rows As Collection

    Dim lastRow As Long
    Dim r As Long, i As Long, j As Long
    Dim pageNo As Long
    Dim pageCount As Long
    Dim outRow As Long
    Dim srcRow As Long

    Dim totalItems As Long
    Dim totalSheets As Long
    Dim oldAlerts As Boolean
    Dim oldScreen As Boolean

    On Error GoTo ErrorHandler

    basePath = ThisWorkbook.Path & "\"
    srcPath = basePath & "OA자산목록.xlsx"
    formPath = basePath & "2026년실사양식.xlsx"
    outPath = basePath & _
        "2026년_OA_창고_자산실사_완성.xlsx"

    depts = Array( _
        "B5층_불용창고", _
        "B5층_가용창고", _
        "8층가용창고")

    If Dir(srcPath) = "" Or Dir(formPath) = "" Then
        MsgBox "원본 또는 양식 파일이 없습니다.", vbExclamation
        Exit Sub
    End If

    oldAlerts = Application.DisplayAlerts
    oldScreen = Application.ScreenUpdating

    Application.ScreenUpdating = False

    ' 원본 및 양식 열기
    Set wbSrc = Workbooks.Open(srcPath, ReadOnly:=True)
    Set wbForm = Workbooks.Open(formPath, ReadOnly:=True)

    Set wsSrc = wbSrc.Worksheets(1)

    ' 양식 시트를 새 통합문서로 복사
    wbForm.Worksheets(1).Copy

    Set wbOut = ActiveWorkbook
    Set wsTemplate = wbOut.Worksheets(1)

    lastRow = wsSrc.Cells( _
        wsSrc.Rows.Count, "D").End(xlUp).Row

    ' 부서별 처리
    For Each dept In depts

        Set rows = New Collection

        ' 대상 부서 행 수집
        For r = 4 To lastRow

            If Not IsError(wsSrc.Cells(r, "D").Value) Then

                If Trim(CStr(wsSrc.Cells(r, "D").Value)) = _
                   CStr(dept) Then

                    rows.Add r

                End If

            End If

        Next r

        If rows.Count > 0 Then

            pageCount = (rows.Count + MAX_ITEMS - 1) \ MAX_ITEMS

            For pageNo = 1 To pageCount

                ' 양식 복사
                wsTemplate.Copy After:= _
                    wbOut.Worksheets(wbOut.Worksheets.Count)

                Set wsNew = wbOut.Worksheets( _
                    wbOut.Worksheets.Count)

                wsNew.Name = CStr(dept) & "(" & pageNo & ")"

                ' 상단 기본정보
                srcRow = CLng(rows(1))

                With wsNew

                    .Range("B3").Value = dept
                    .Range("I3").Value = wsSrc.Cells(srcRow, "B").Value
                    .Range("L3").Value = wsSrc.Cells(srcRow, "A").Value

                    .Range("B4").Value = wsSrc.Cells(srcRow, "Q").Value
                    .Range("I4").Value = wsSrc.Cells(srcRow, "R").Value

                    ' 장비 데이터 9~31행
                    For j = 1 To MAX_ITEMS

                        i = (pageNo - 1) * MAX_ITEMS + j

                        If i > rows.Count Then Exit For

                        srcRow = CLng(rows(i))
                        outRow = 8 + j

                        ' 원본 E~J -> 양식 A~F
                        .Cells(outRow, "A").Value = _
                            wsSrc.Cells(srcRow, "E").Value

                        .Cells(outRow, "B").Value = _
                            wsSrc.Cells(srcRow, "G").Value

                        .Cells(outRow, "C").Value = _
                            wsSrc.Cells(srcRow, "H").Value

                        .Cells(outRow, "D").Value = _
                            wsSrc.Cells(srcRow, "I").Value

                        .Cells(outRow, "E").Value = _
                            wsSrc.Cells(srcRow, "F").Value

                        .Cells(outRow, "F").Value = _
                            wsSrc.Cells(srcRow, "J").Value

                    Next j

                    ' 실사 연월 자동 입력
                    .Range("A38").Value = _
                        "실사 일자: " & _
                        Format(Date, "yyyy년 m월")

                End With

                totalSheets = totalSheets + 1

            Next pageNo

            totalItems = totalItems + rows.Count

        End If

    Next dept

    If totalSheets = 0 Then
        MsgBox "조건에 해당하는 장비가 없습니다.", vbExclamation
        GoTo CleanUp
    End If

    ' 원본 템플릿 시트 삭제
    Application.DisplayAlerts = False
    wsTemplate.Delete
    Application.DisplayAlerts = oldAlerts

    ' 결과 저장
    If Dir(outPath) <> "" Then
        MsgBox "결과 파일이 이미 존재합니다." & vbCrLf & _
               "기존 파일을 이동하거나 이름을 변경한 뒤 재실행하세요.", _
               vbExclamation
        GoTo CleanUp
    End If

    wbOut.SaveAs Filename:=outPath, _
        FileFormat:=xlOpenXMLWorkbook

    MsgBox "창고 자산실사 양식 생성 완료!" & vbCrLf & _
           "총 장비: " & totalItems & "대" & vbCrLf & _
           "생성 시트: " & totalSheets & "개" & vbCrLf & _
           "저장 경로: " & outPath, vbInformation

CleanUp:
    On Error Resume Next
    If Not wbSrc Is Nothing Then wbSrc.Close False
    If Not wbForm Is Nothing Then wbForm.Close False
    Application.DisplayAlerts = oldAlerts
    Application.ScreenUpdating = oldScreen
    Exit Sub

ErrorHandler:
    MsgBox "오류 " & Err.Number & vbCrLf & _
           Err.Description, vbCritical
    Resume CleanUp

End Sub
