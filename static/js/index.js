function compute(){
    let deposit = parseFloat(document.getElementById('deposit').value)
    if (isNaN(deposit)) {
        deposit = 1
        document.getElementById('deposit').value = 1
    }
    let hydratePeriod = parseFloat(document.getElementById('hydrate-period').value)
    if (isNaN(hydratePeriod)) {
        hydratePeriod = 1
        document.getElementById('hydrate-period').value = 1
    }
    let dripPrice = parseFloat(document.getElementById('drip-price').value)

    $.ajax({
       url: 'http://www.drip-calculator.com/compute',
        // url: 'compute',
        type: 'get',
        data: {
            deposit: deposit,
            hydrate_period: hydratePeriod,
            drip_price: isNaN(dripPrice) ? null : dripPrice
        },
        success: function(res){
            if (res.error != null) {
                handle_error(res)
                return
            } else {
                clean_error_msg()
            }

            document.getElementById('drip-price').value = res.body.drip_price

            let tableDiv = document.getElementById('dataTableDiv')

            let oldTable = document.getElementById('dataTable')
            oldTable.remove()
            let newTable = generateTable('dataTable', res.body.data_overtime, 'DRIP');
            tableDiv.appendChild(newTable)

            let oldUsdTable = document.getElementById('dataTableUsd')
            oldUsdTable.remove()
            let newUsdTable = generateTable('dataTableUsd', res.body.data_overtime_usd, '$');
            tableDiv.appendChild(newUsdTable)
        }
    });
}

function handle_error(response){
    document.getElementById('form-error').innerHTML = response.message
}

function clean_error_msg(){
    document.getElementById('form-error').innerHTML = null
}

function generateTable(tableId, dataOvertime, unit){
    // New table
    let table = document.createElement('table');
    table.setAttribute('id', tableId);
    table.setAttribute('class', 'dataTable');

    // First row is for days 0, 30, 60, 90, ... 365
    let daysTr = document.createElement('tr');
    table.appendChild(daysTr)

    let daysTh = document.createElement('th');
    daysTh.innerHTML = 'Days'
    daysTr.appendChild(daysTh)

    for (let i=0; i<365; i=i+30) {
        let tdElement = document.createElement('td');
        tdElement.style.cssText = 'font-weight:bold;color:#fff';
        tdElement.innerHTML = i.toString();
        daysTr.appendChild(tdElement);
    }
    let tdElement365 = document.createElement('td');
    tdElement365.style.cssText = 'font-weight:bold;color:#fff';
    tdElement365.innerHTML = '365';
    daysTr.appendChild(tdElement365)

    // Second row is for interests earned
    let interestTr = document.createElement('tr');
    table.appendChild(interestTr)

    let interstTh = document.createElement('th');
    interstTh.innerHTML = 'Interest ' + '(' + unit + ')'
    interestTr.appendChild(interstTh)

    for (let k of Object.keys(dataOvertime['interest'])) {
        let tdElement = document.createElement('td');
        tdElement.innerHTML = dataOvertime['interest'][k].toLocaleString('us-US');
        interestTr.appendChild(tdElement)
    }

    // Third row is for tax payed
    let taxTr = document.createElement('tr');
    table.appendChild(taxTr)

    let taxTh = document.createElement('th');
    taxTh.innerHTML = 'Tax ' + '(' + unit + ')'
    taxTr.appendChild(taxTh)

    for (let k of Object.keys(dataOvertime['tax'])) {
        let tdElement = document.createElement('td');
        tdElement.innerHTML = dataOvertime['tax'][k].toLocaleString('us-US');
        taxTr.appendChild(tdElement)
    }

    // Forth row is for total
    let totalTr = document.createElement('tr');
    table.appendChild(totalTr)

    let totalTh = document.createElement('th');
    totalTh.innerHTML = 'Total ' + '(' + unit + ')'
    totalTr.appendChild(totalTh)

    for (let k of Object.keys(dataOvertime['total'])) {
        let tdElement = document.createElement('td');
        tdElement.innerHTML = dataOvertime['total'][k].toLocaleString('us-US');
        totalTr.appendChild(tdElement)
    }

    return table
}
