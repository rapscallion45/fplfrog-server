import app from "./app";
import runDataScraperOnTimeout from "./scraper/scraper";
import config from "./utils/config";

app.get("/", (_, res) => {
  res.status(200).send("FPL Frog Data Server running ok. 🐸⚽");
});

app.listen(config.PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Running on port ${config.PORT}`);

  runDataScraperOnTimeout();
});
