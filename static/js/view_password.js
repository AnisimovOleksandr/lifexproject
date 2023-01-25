function myFunction(y) {
  var x = document.getElementById("myInput");
  x.type = (x.type === "password") ? "text" : "password";
  
  y.classList.toggle("fa-eye-slash");
}
