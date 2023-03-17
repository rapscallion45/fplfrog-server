import { PythonShell } from "python-shell";

/* sets when the first call should be made, i.e on the hour (ms) */
const FIRST_RUN_TIMEOUT = 60 * 60 * 1000;

/* interval between data scraper calls (ms) */
const INTERVAL = 4 * 60 * 60 * 1000;

/* run data scraper */
const runDataScraper = async () => {
  // eslint-disable-next-line no-console
  console.log("Running data scraper...");

  /* run data scraper Python script */
  await PythonShell.run("src/scraper/xgdata_scraper.py", undefined);

  // eslint-disable-next-line no-console
  console.log(
    `Data scraper completed successfully at ${new Date().toLocaleString()}`
  );
};

/* manual cron scheduler (4 hours) */
const runDataScraperOnTimeout = () => {
  const currentDate = new Date();
  const currentHourMSecs =
    (currentDate.getMinutes() * 60 + currentDate.getSeconds()) * 1000 +
    currentDate.getMilliseconds();

  const firstCall = FIRST_RUN_TIMEOUT - currentHourMSecs;

  setTimeout(() => {
    runDataScraper();
    setInterval(runDataScraper, INTERVAL);
  }, firstCall);
};

export default runDataScraperOnTimeout;
