import dotenv from "dotenv";

/* initialise dotenv */
dotenv.config();

const PORT = (process.env.PORT as string) || "3000";

export default {
  PORT,
};
