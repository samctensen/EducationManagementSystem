import { $ } from "/static/jquery/src/jquery.js";

export function say_hi(elt) {
    console.log("Say hi to", elt);
}
  
export function make_table_sortable(header, tbody) {
    header.siblings().removeClass("sort-asc sort-desc");
    if (header.hasClass("sort-asc")) {
        header.removeClass("sort-asc");
        header.addClass("sort-desc");
    }
    else if (header.hasClass("sort-desc")) {
        header.removeClass("sort-desc");
    }
    else {
        header.addClass("sort-asc");
    }
    let rows = tbody.find("tr").toArray();
    if (header.is(':last-child')) {
        rows.sort(compareGrades);
    }
    else {
        rows.sort(compareDates);
    }
    $(rows).appendTo("tbody");
}

function compareGrades(a, b) {
    let aVal = parseInt(a.lastElementChild.innerText);
    let bVal = parseInt(b.lastElementChild.innerText);
    if ($(a).parent().siblings("thead").children("tr").children("th:last").hasClass("sort-asc")) {
        if (isNaN(aVal) && !isNaN(bVal)) {
            return 1;
        }
        if (isNaN(bVal) && !isNaN(aVal)) {
            return -1;
        }
        if (isNaN(aVal) && isNaN(bVal)) {
            return 0;
        }
        return aVal-bVal;
    }
    else if ($(a).parent().siblings("thead").children("tr").children("th:last").hasClass("sort-desc")) {
        return parseInt(b.lastElementChild.innerText) - parseInt(a.lastElementChild.innerText);
    }
    else {
        return $(a).data("index") - $(b).data("index");
    }
}

function compareDates(a, b) {
    if ($(a).parent().siblings("thead").children("tr").children("th:nth-child(2)").hasClass("sort-asc")) {
        return $(a).data("value") - $(b).data("value");
    }
    else if ($(a).parent().siblings("thead").children("tr").children("th:nth-child(2)").hasClass("sort-desc")) {
        return $(b).data("value") - $(a).data("value");
    }
    else {
        return $(a).data("index") - $(b).data("index");
    }
}

export function make_form_async(form, csrftoken) {
    let actionURL = form.attr('action');
    let enctype = form.attr('enctype');
    let formData = new FormData(form[0])
    form.find('#fileSubmission').prop("disabled",true);
    form.find('#submitButton').prop("disabled",true);
    let nuts = await $.ajax({
        url: actionURL,
        data: formData,
        type: 'POST',
        processData: false,
        contentType: false,
        mimeType: enctype,
        success: function(response) {
            // Handle the success response from the server
            let submissionComment = $(response).children("div.action-card");
            submissionComment.children("p#submissionComment").prepend("<p style='margin: 0'>Upload succeeded!</p>");
            $("div.action-card").replaceWith(submissionComment);
            $("form").remove();
            $("input").remove();
            $("button").remove();
        },
        error: function(error) {
            console.log(error);
        }
    })
}

export function make_grade_hypothesized(table) {
    var button = $('<button>').text('Hypothesize');
    button.on('click', function() {
        let rows = table.children("tbody").children("tr").toArray();
        if ($(this).text() == ("Hypothesize")) {
            button.text('Actual grades');
            table.addClass("hypothesized");
            let finalGrade = table.children("tfoot").children("tr").children("th:last");
            finalGrade.attr('data-value', finalGrade.text());
            rows.forEach(function(row) {
                let grade = $(row).children("td:last");
                grade.attr('data-value', grade.text());
                if (grade.text() == 'Ungraded' || grade.text() == 'Not Due') {
                grade.text("");
                let inputBox =  $('<input type="number">');
                inputBox.on( "change", function() {
                    changeGrade(table)
                });
                grade.append(inputBox);
            }
            });
            changeGrade(table)
        }
        else {
            button.text('Hypothesize');
            table.removeClass("hypothesized");
            rows.forEach(function(row) {
                let grade = $(row).children("td:last");
                grade.children("input").remove();
                grade.text(grade.data("value"));
            });
            changeGrade(table)
        }
    });
    table.before(button);
}

export function changeGrade(table) {
    let availableGradePoints = 0;
    let earnedGradePoints = 0;
    let rows = table.children("tbody").children("tr").toArray();
    rows.forEach(function(row) {
        let grade = $(row).children("td:last");
        if (grade.children().length > 0) {
            let score = parseInt(grade.children("input").val());
            if (!isNaN(score)) {
                availableGradePoints = availableGradePoints + grade.data('weight');
                earnedGradePoints = earnedGradePoints + (score / 100 * grade.data('weight'));
            }
        }
        else if (grade.text() != "Missing") {
            let score = parseInt(grade.text().substring(0, grade.text().length - 1));
            if (!isNaN(score)) {
                availableGradePoints = availableGradePoints + grade.data('weight');
                earnedGradePoints = earnedGradePoints + (score / 100 * grade.data('weight'));
            }
        }
        else if (grade.text() == "Missing") {
            availableGradePoints = availableGradePoints + grade.data('weight');
        }
    });
    let finalGrade = ((earnedGradePoints / availableGradePoints * 100).toFixed(1)) + "%";
    table.children("tfoot").children("tr:last").children("th:last").text(finalGrade);
}