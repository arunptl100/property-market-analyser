function updateTextInput(val) {
  document.getElementById('interval_text').innerHTML= "Scanning time interval: " + val + " hour(s)";
}


$(document).ready(function() {
  $("#p-table tr").click(function() {
    // console.log("Clicked", this);
    // get the current row
    var currentRow=$(this).closest("tr");
    var col1=currentRow.find("td:eq(0)").text(); // get current row 1st TD value
    $.ajax({
      url: '/get-prop-details',
      data: {"id": col1},
      type: 'POST',
      dataType: 'json',
      success: function(response) {
        console.log(response);
        htmlData = '<ul><li><b>Address</b>:<br>'+ response.displayable_address+'</li><li><b>agent link</b>:<br> '+response.details_url+'</li></ul>';
        $("#myModal").find('.modal-body').html(htmlData)
        $("#myModal").modal("show");
      },
      error: function(error) {
        console.log(error);
      }
    });
  });
});
