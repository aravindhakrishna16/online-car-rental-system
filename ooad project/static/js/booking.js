/* ==========================================================
   DRIVEEASE - BOOKING & PAYMENT INTERACTION LOGIC
   Live fare calculator, date validation, and payment tabs
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {
  const startDateInput = document.getElementById("bookingStartDate");
  const endDateInput = document.getElementById("bookingEndDate");
  const carIdInput = document.getElementById("bookingCarId");

  // Ensure minimum date is today
  const today = new Date().toISOString().split("T")[0];
  if (startDateInput) {
    if (!startDateInput.min) startDateInput.min = today;
    if (!startDateInput.value) startDateInput.value = today;

    // Set tomorrow for end date if not set
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 2);
    const tomorrowStr = tomorrow.toISOString().split("T")[0];
    if (endDateInput && !endDateInput.value) {
      endDateInput.min = today;
      endDateInput.value = tomorrowStr;
    }
  }

  const kmInput = document.getElementById("estimatedKm");

  // Real-time live fare estimate & availability check
  const updateFareEstimate = async () => {
    if (!startDateInput || !endDateInput || !carIdInput) return;

    const startVal = startDateInput.value;
    const endVal = endDateInput.value;
    const carId = carIdInput.value;
    const kmVal = kmInput ? (parseFloat(kmInput.value) || 100) : 100;

    if (!startVal || !endVal || !carId) return;

    // Adjust end date min
    endDateInput.min = startVal;
    if (endVal < startVal) {
      endDateInput.value = startVal;
    }

    try {
      const resp = await fetch("/api/calculate-fare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          car_id: carId,
          start_date: startVal,
          end_date: endDateInput.value,
          estimated_km: kmVal
        })
      });

      const data = await resp.json();
      if (data.success) {
        // Update DOM elements if present
        const daysEl = document.getElementById("calcDays");
        const baseFareEl = document.getElementById("calcBaseFare");
        const kmChargesEl = document.getElementById("calcKmCharges");
        const kmLabelEl = document.getElementById("calcKmLabel");
        const taxesEl = document.getElementById("calcTaxes");
        const totalEl = document.getElementById("calcTotal");
        const availBadge = document.getElementById("availabilityBadge");
        const bookSubmitBtn = document.getElementById("btnSubmitBooking");

        if (daysEl) daysEl.innerText = `${data.days} Day${data.days > 1 ? 's' : ''}`;
        if (baseFareEl) baseFareEl.innerText = `₹${Math.round(data.base_fare).toLocaleString('en-IN')}`;
        if (kmChargesEl) kmChargesEl.innerText = `₹${Math.round(data.km_charges).toLocaleString('en-IN')}`;
        if (kmLabelEl) kmLabelEl.innerText = `${data.estimated_km} km × ₹${Math.round(data.price_per_km)}/km`;
        if (taxesEl) taxesEl.innerText = `₹${Math.round(data.taxes).toLocaleString('en-IN')}`;
        if (totalEl) totalEl.innerText = `₹${Math.round(data.grand_total).toLocaleString('en-IN')}`;

        // If on car_details page, keep the book button URL updated with query params
        if (bookSubmitBtn && bookSubmitBtn.tagName === 'A' && bookSubmitBtn.getAttribute('href')) {
          const rawHref = bookSubmitBtn.getAttribute('href');
          if (rawHref.includes('/book/')) {
            const baseUrl = rawHref.split('?')[0];
            bookSubmitBtn.href = `${baseUrl}?start_date=${encodeURIComponent(startVal)}&end_date=${encodeURIComponent(endDateInput.value)}&estimated_km=${encodeURIComponent(kmVal)}`;
          }
        }

        if (availBadge) {
          if (data.is_available) {
            availBadge.className = "alert alert-success";
            availBadge.style.display = "block";
            availBadge.innerHTML = `<i class="fa fa-circle-check"></i> Available for selected dates!`;
            if (bookSubmitBtn) bookSubmitBtn.disabled = false;
          } else {
            availBadge.className = "alert alert-danger";
            availBadge.style.display = "block";
            availBadge.innerHTML = `<i class="fa fa-triangle-exclamation"></i> Vehicle is already booked for these dates. Please choose different dates.`;
            if (bookSubmitBtn) bookSubmitBtn.disabled = true;
          }
        }
      }
    } catch (err) {
      console.error("Live fare estimation error:", err);
    }
  };

  if (startDateInput && endDateInput) {
    startDateInput.addEventListener("change", updateFareEstimate);
    endDateInput.addEventListener("change", updateFareEstimate);
    if (kmInput) {
      kmInput.addEventListener("input", updateFareEstimate);
      kmInput.addEventListener("change", updateFareEstimate);
    }
    // Initial calculate
    updateFareEstimate();
  }

  // Payment Tabs Logic
  const paymentTabs = document.querySelectorAll(".payment-method-tab");
  const paymentSections = document.querySelectorAll(".payment-method-section");
  const selectedMethodInput = document.getElementById("selectedPaymentMethod");

  paymentTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const method = tab.getAttribute("data-method");
      
      paymentTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      paymentSections.forEach(sec => {
        if (sec.id === `section-${method}`) {
          sec.style.display = "block";
        } else {
          sec.style.display = "none";
        }
      });

      if (selectedMethodInput) selectedMethodInput.value = method;
    });
  });
});
