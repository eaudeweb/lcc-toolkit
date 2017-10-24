$(document).ready(function() {
  $('.open-sidebar').click(function(){
    $(this).parent().toggleClass('active')
    $(this).find('span').toggleClass('active');
  })
});
