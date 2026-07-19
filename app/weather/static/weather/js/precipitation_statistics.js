(() => {
    const openButton = document.querySelector(
        "#open-statistics-modal",
    );
    const modal = document.querySelector("#statistics-modal");

    if (
        !(openButton instanceof HTMLButtonElement) ||
        !(modal instanceof HTMLDialogElement)
    ) {
        return;
    }

    const statusElement = modal.querySelector(
        "#statistics-status",
    );
    const resultsElement = modal.querySelector(
        "#statistics-results",
    );
    const periodElement = modal.querySelector(
        "#statistics-period",
    );
    const countElement = modal.querySelector(
        "#statistics-count",
    );
    const snowElement = modal.querySelector(
        "#statistics-snow",
    );
    const rainElement = modal.querySelector(
        "#statistics-rain",
    );
    const totalElement = modal.querySelector(
        "#statistics-total",
    );
    const closeButtons = modal.querySelectorAll(
        "[data-modal-close]",
    );

    if (
        !(statusElement instanceof HTMLElement) ||
        !(resultsElement instanceof HTMLElement) ||
        !(periodElement instanceof HTMLElement) ||
        !(countElement instanceof HTMLElement) ||
        !(snowElement instanceof HTMLElement) ||
        !(rainElement instanceof HTMLElement) ||
        !(totalElement instanceof HTMLElement)
    ) {
        return;
    }

    const numberFormatter = new Intl.NumberFormat("pl-PL", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    const monthFormatter = new Intl.DateTimeFormat("pl-PL", {
        month: "long",
        year: "numeric",
        timeZone: "UTC",
    });

    const resetModal = () => {
        statusElement.textContent = "Pobieranie danych...";
        statusElement.classList.remove("statistics-status-error");

        resultsElement.hidden = true;
        periodElement.textContent = "";

        countElement.textContent = "—";
        snowElement.textContent = "—";
        rainElement.textContent = "—";
        totalElement.textContent = "—";
    };

    const displayError = (message) => {
        statusElement.textContent = message;
        statusElement.classList.add("statistics-status-error");

        resultsElement.hidden = true;
    };

    const displayStatistics = (data) => {
        const year = Number(data.period.year);
        const month = Number(data.period.month);

        const monthDate = new Date(
            Date.UTC(year, month - 1, 1),
        );

        periodElement.textContent =
            monthFormatter.format(monthDate);

        countElement.textContent = String(
            data.measurement_count,
        );

        snowElement.textContent = numberFormatter.format(
            Number(data.averages.snow),
        );

        rainElement.textContent = numberFormatter.format(
            Number(data.averages.rain),
        );

        totalElement.textContent = numberFormatter.format(
            Number(data.averages.total),
        );

        statusElement.textContent = "";
        resultsElement.hidden = false;
    };

    const loadStatistics = async () => {
        const statisticsUrl =
            openButton.dataset.statisticsUrl;

        if (!statisticsUrl) {
            displayError(
                "Nie skonfigurowano adresu statystyk.",
            );
            return;
        }

        try {
            const response = await fetch(statisticsUrl, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
                credentials: "same-origin",
                cache: "no-store",
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error?.message ??
                        "Nie udało się pobrać statystyk.",
                );
            }

            displayStatistics(data);
        } catch (error) {
            console.error(
                "Błąd pobierania statystyk:",
                error,
            );

            const message =
                error instanceof Error
                    ? error.message
                    : "Nie udało się pobrać statystyk.";

            displayError(message);
        }
    };

    openButton.addEventListener("click", () => {
        resetModal();
        modal.showModal();

        void loadStatistics();
    });

    closeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            modal.close();
        });
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            modal.close();
        }
    });
})();