
document.getElementById("submitDate").addEventListener("click", function () {
    // Get the selected date
    const selectedDate = $("#datePicker").val();
    const outputDiv = document.getElementById('output');

    if (!selectedDate) {
        $("#date").text("Please select a date!");
        outputDiv.innerHTML = '';
        return;
    }

    outputDiv.innerHTML = 'Fetching data...';

    // Send the date to the backend
    $.ajax({
        url: "/submit-date",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ date: selectedDate }),
        success: function (response) {
            // Clear the output div
            outputDiv.innerHTML = '';

            // Display the result from the backend
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            const dateObject = new Date(selectedDate + "T00:00");
            $("#date").text("You have selected the date: " + dateObject.toLocaleDateString('en-US', options));
        
            // Extract the response data
            const { trading_strategy, next_five_business_days, highest_price, lowest_price, average_price } = response;

            // Display the highest, lowest, and average prices in a table
            let priceTableHTML = `
                <table border="1">
                    <tr>
                        <th>Price Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Highest Price</td>
                        <td>${parseFloat(highest_price.toFixed(2))}</td>
                    </tr>
                    <tr>
                        <td>Lowest Price</td>
                        <td>${parseFloat(lowest_price.toFixed(2))}</td>
                    </tr>
                    <tr>
                        <td>Average Price</td>
                        <td>${parseFloat(average_price.toFixed(2))}</td>
                    </tr>
                </table>
            `;
        
            // Start building the table
            let tableHTML = `
                <table border="1">
                    <tr>
                        <th>Next Five Business Days</th>
                        <th>Trading Strategy</th>
                    </tr>
            `;
            // Ensure both arrays have the same length (or handle mismatched lengths)
            const maxLength = Math.max(trading_strategy.length, next_five_business_days.length);
            for (let i = 0; i < maxLength; i++) {
                tableHTML += `
                    <tr>
                        <td>${next_five_business_days[i].replace(" 00:00:00 GMT", "") || ''}</td>
                        <td>${trading_strategy[i] || ''}</td>
                    </tr>
                `;
            }
            // Close the table
            tableHTML += '</table>';

            // Set innerHTML of the output div
            outputDiv.innerHTML += '<h2>Predicted prices for the next five business days (in USD) are:</h2>';
            outputDiv.innerHTML += priceTableHTML;
            outputDiv.innerHTML += '<h2>Recommended trading strategies:</h2>';
            outputDiv.innerHTML += tableHTML;
        },
        error: function () {
            $("#date").text("An error occurred.");
            outputDiv.innerHTML = '';
        },
    });
});
