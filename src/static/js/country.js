$(document).ready(function() {
    $('#country').change(function() {

      var country = $('#country').val();

      // Make Ajax Request and expect JSON-encoded data
      $.getJSON(
        '/get_city' + '/' + country,
        function(data) {

          // Remove old options
          $('#city').find('option').remove();                                

          // Add new items
          $.each(data, function(key, val) {
            var option_item = '<option value="'+ val.id +'">' + val.name + '</option>'
            $('#city').append(option_item);
          });
        }
      );
    });
  });