function create_line_chart(name, chart_data, xkey, ykeys, labels){
    window.line_chart = new Morris.Line({
        // ID of the element in which to draw the chart.
        element: name,
        // Chart data records -- each entry in this array corresponds to a point on
        // the chart.
        data: chart_data,
        // The name of the data record attribute that contains x-values.
        xkey: xkey,
        // A list of names of data record attributes that contain y-values.
        ykeys: ykeys,
        // Labels for the ykeys -- will be displayed when you hover over the
        // chart.
        labels: labels,
        parseTime: false,
        resize: true,
        redraw: true
      });
}


function create_bar_chart(name, chart_data){
    window.bar_chart = new Morris.Bar({
        // ID of the element in which to draw the chart.
        element: name,
        data: chart_data,
        xkey: 'y',
        ykeys: ['a'],
        labels: ['Series A'],
        resize: true,
        redraw: true
      });
}


window.onload = function(){
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  });
}

window.setTimeout(function() {
  $(".autofade").fadeTo(500, 0).slideUp(500, function(){
      $(this).remove(); 
  });
}, 4000);
