/*
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
*/
document.addEventListener('DOMContentLoaded', function () {
    //This list is not ordered. Better to make use of rest api (generics/listview: a serializer>>a view). But how to show on html, how to delete
    $.getJSON( "consulta", function( data ) {
      var items = [];
      $.each( data, function( key, val ) {
        items.push(
            "<div class=\"custom-control custom-checkbox\"><input type=\"checkbox\" class=\"custom-control-label\" id=\"" + val.id + "\" name=\"consultas\"><label class=\"list-group-item\" data-color=\"info\" id-user=\"" + val.userCode + "\" >" + val.title +" - " + val.start + "</label></div>" );
      });

      $( "<div/>", {
        'class': '',
        html: items.join( "" )
      }).appendTo( "t-body" );
    });


    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'pt-br',
        plugins: ['interaction', 'dayGrid', 'timeGrid'],
        header: {
          left: 'prev,next today addEventButton',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek',
        },
        editable: true,
        eventStartEditable: true,
        eventLimit: true,
        slotDuration: '00:15',
        minTime: '06:00',
        maxTime: '19:00',

        //events: [{'id': 'a', 'title': 'my event', 'start': '2020-03-01'}],

        events: {
            url: 'agenda',
            error: function() {
            $('#script-warning').show();
            }
        },
        
        customButtons: {
          addEventButton: {
            text: 'add event...',
            click: function() {
              var dateStr = prompt('Enter a date in YYYY-MM-DDT00:00 format');
              var date = new Date(dateStr);
              if (!isNaN(date.valueOf())) {
                calendar.addEvent({
                  title: 'dynamic event',
                  start: date,
                  allDay: true
                });

              } else {
                alert('Invalid date.');
              }
            }
        }
    },

        eventRender: function (info) {
            console.log(info.event.extendedProps);
            console.log(info.event);
        },

        extraParams: function () {
            return {
                cachebuster: new Date().valueOf()
            };
        },

        eventClick: function (info) {
            info.jsEvent.preventDefault();
            $('#visualizar #id').text(info.event.id);
            $('#visualizar #id').val(info.event.id);
            $('#visualizar #title').text(info.event.title);
            $('#visualizar #title').val(info.event.title);
            $('#visualizar #start').text(info.event.start);
            $('#visualizar #start').val(info.event.start);

            $('#visualizar').modal('show');
        },

        selectable: true,
        select: function (info) {
            $('#cadastrar #start').val(info.start.toLocaleString());
            $('#cadastrar #end').val(info.end.toLocaleString());
            $('#cadastrar').modal('show');
        },

        eventDrop: function(info) {
            info.jsEvent.preventDefault();
            $('#visualizar').modal('show');
        }
    });

    calendar.render();
});

//Mascara para o campo data e hora
function DataHora(evento, objeto) {
    var keypress = (window.event) ? event.keyCode : evento.which;
    campo = eval(objeto);
    if (campo.value == '00/00/0000 00:00:00') {
        campo.value = "";
    }

    caracteres = '0123456789';
    separacao1 = '/';
    separacao2 = ' ';
    separacao3 = ':';
    conjunto1 = 2;
    conjunto2 = 5;
    conjunto3 = 10;
    conjunto4 = 13;
    conjunto5 = 16;
    if ((caracteres.search(String.fromCharCode(keypress)) != -1) && campo.value.length < (19)) {
        if (campo.value.length == conjunto1)
            campo.value = campo.value + separacao1;
        else if (campo.value.length == conjunto2)
            campo.value = campo.value + separacao1;
        else if (campo.value.length == conjunto3)
            campo.value = campo.value + separacao2;
        else if (campo.value.length == conjunto4)
            campo.value = campo.value + separacao3;
        else if (campo.value.length == conjunto5)
            campo.value = campo.value + separacao3;
    } else {
        event.returnValue = false;
    }
}

$(document).ready(function () {
    $("#addevent").on("submit", function (event) {
        event.preventDefault();
        $.ajax({
            method: "POST",
            url: "cad_event.php",
            data: new FormData(this),
            contentType: false,
            processData: false,
            success: function (retorna) {
                if (retorna['sit']) {
                    location.reload();
                } else {
                    $("#msg-cad").html(retorna['msg']);
                }
            }
        })
    });
    
    $('.btn-canc-vis').on("click", function(){
        $('.visevent').slideToggle();
        $('.formedit').slideToggle();
    });
    
    $('.btn-canc-edit').on("click", function(){
        $('.formedit').slideToggle();
        $('.visevent').slideToggle();
    });
    
    $("#editevent").on("submit", function (event) {
        event.preventDefault();
        $.ajax({
            method: "POST",
            url: "edit_event.php",
            data: new FormData(this),
            contentType: false,
            processData: false,
            success: function (retorna) {
                if (retorna['sit']) {
                    location.reload();
                } else {
                    $("#msg-edit").html(retorna['msg']);
                }
            }
        })
    });


    $("#delevent").on("submit", function (event) {
            var okToDel = prompt("Digite s para excluir:");
            if (okToDel == 's') {
            event.preventDefault();
            $.ajax({
                method: "POST",
                url: "del_event.php",
                data: new FormData(this),
                contentType: false,
                processData: false,
                success: function (retorna) {
                    if (retorna['sit']) {
                        location.reload();
                    } else {
                        $("#msg-del").html(retorna['msg']);
                    }
                }
            })
        } else {location.reload();}
    });
});

function deletar_consulta(){
  var pacote = document.getElementsByName('consultas');
    for (var i = 0; i < pacote.length; i++){
        if ( pacote[i].checked ) {
            console.log(pacote[i])
            if(pacote[i].id !== null){
                var settings = {
                  "async": true,
                  "crossDomain": true,
                  "url": "/consulta/deletar",
                  "method": "POST",
                  "headers": {
                    "content-type": "application/x-www-form-urlencoded",
                  },
                  "data": {
                    "codigo_consulta": pacote[i].id,
                  }
                }
                $.ajax(settings).done(function (response) {
                    window.location.reload()
                });
            }
        }
    }

}

function alterar_consulta(){
  var pacote = document.getElementsByName('consultas');
  var data = document.getElementsByName('data_alterar');
  var time = document.getElementsByName('time_alterar');
  var comentario = document.getElementsByName('comentario_alterar');
  console.log(data, time, comentario)
    for (var i = 0; i < pacote.length; i++){
        if ( pacote[i].checked ) {
            console.log(pacote[i])
            if(pacote[i].id !== null){
                var settings = {
                  "async": true,
                  "crossDomain": true,
                  "url": "/consulta/alterar",
                  "method": "POST",
                  "headers": {
                    "content-type": "application/x-www-form-urlencoded",
                  },
                  "data": {
                    "codigo_consulta": pacote[i].id,
                    "data": data[0].value,
                    "time": time[0].value,
                    "comentario": comentario[0].value,
                  }
                }
                $.ajax(settings).done(function (response) {
                    window.location.reload()
                });
            }
        }
    }

}
