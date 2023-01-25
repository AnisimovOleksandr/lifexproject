$(function() {
    var cardNumber = $('#cardNumber');
    var cardNumberField = $('#card-number-field');
    cardNumber.payform('formatCardNumber');
    cardNumber.keyup(function() {
        if ($.payform.validateCardNumber(cardNumber.val()) == false) {
            cardNumberField.addClass('has-error');
        }
        else {
            cardNumberField.removeClass('has-error');
            cardNumberField.addClass('has-success');
        }
    });
});

