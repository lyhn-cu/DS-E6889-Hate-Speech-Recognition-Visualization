google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);
var words_list = res["list"];
function drawChart() {

    // Create the data table.
    var barchart = new google.visualization.DataTable();
    barchart.addColumn('string', 'Topping');
    barchart.addColumn('number', 'Slices');


    barchart.addRows(words_list)


    // Set chart options
    var options = {'title':'Word Count',
                   'width':800,
                   'height':800};

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
    chart.draw(barchart, options);
  }