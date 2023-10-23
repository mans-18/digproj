var data = new Date();
var dia     = data.getDate();
var mes     = data.getMonth();
var ano4    = data.getFullYear();
var str_data = ano4 + '-' + (mes+1) + '-' +dia;
if (dia < 10) {
    var str_data = ano4 + '-' + (mes+1) + '-0' +dia;
}else{
    var str_data = ano4 + '-' + (mes+1) + '-' +dia;
}

$(document).ready(function() {

    $('#calendar').fullCalendar({
    header: {
    left: 'prev,next today',
    center: 'title',
    right: 'agendaWeek,agendaDay'
    },
    defaultDate: str_data,
    editable: false,
    navLinks: true, // can click day/week names to navigate views
    eventLimit: true, // allow "more" link when too many events
    events: {
        url: '/agenda',
        error: function() {
        $('#script-warning').show();
        }
    },
    loading: function(bool) {
        $('#loading').toggle(bool);
    }
    });
});