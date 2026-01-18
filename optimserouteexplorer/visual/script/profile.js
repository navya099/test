window.profileChart = null;

function showProfile(planElevs, groundElevs){
    // canvas와 실제 픽셀 크기 조정
    var canvas = document.getElementById('profile_canvas');
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;

    var ctx = canvas.getContext('2d');

    if(window.profileChart) window.profileChart.destroy();

    var planData = planElevs.map(([sta, elev]) => ({ x: sta, y: elev }));
    var groundData = groundElevs.map(([sta, elev]) => ({ x: sta, y: elev }));

    window.profileChart = new Chart(ctx,{
        type:'line',
        data:{datasets:[
            {label:'Plan', data:planData, borderColor:'red', fill:false},
            {label:'Ground', data:groundData, borderColor:'blue', fill:false}
        ]},
        options:{
            responsive:false,
            maintainAspectRatio:false,
            plugins:{legend:{display:true}},
            scales:{
                x:{
                    type:'linear',
                    position:'bottom',
                    title:{display:true, text:'Distance (km)'}
                },
                y:{
                    title:{display:true, text:'Elevation (m)'}
                }
            }
        }
    });
}