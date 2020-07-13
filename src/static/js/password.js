$(function(){

    var mayus   = new RegExp("^(?=.*[A-Z])");
    var special = new RegExp("^(?=.*[!@#$&*])");
    var numbers = new RegExp("^(?=.*[0-9])");
    var lower   = new RegExp("^(?=.*[a-z])");
    var len     = new RegExp("^(?=.{8,})");

    $("#password").on("keyup", function(){

        var pass =$("#password").val();

        if(mayus.test(pass) && special.test(pass) && numbers.test(pass)  && lower.test(pass)  && len.test(pass)){
            $("#message").text("Contraseña Segura").css("color", "green");
        }else{
            $("#message").text("Contraseña Insegura: debe tener mínimo 8 caracteres, una letra mayúscula, un numero y un carácter especial").css("color", "red");
        }

    });

});

