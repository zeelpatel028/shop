const togglePassword = document.querySelector("#toggle-password");
const passwordInput = document.querySelector("#password-input");

if (togglePassword && passwordInput) {
    togglePassword.addEventListener("click", function () {
        // Toggle the type attribute
        const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
        passwordInput.setAttribute("type", type);

        // Toggle the eye icon
        this.classList.toggle("fa-eye");
        this.classList.toggle("fa-eye-slash");
    });
}
