document.addEventListener('DOMContentLoaded', function() {
    jQuery(function($){
            $('.male').each(function(i){
            $(this).click(function(){ $('#male_dd').eq(i).toggle();
            });
           });
       });
});

