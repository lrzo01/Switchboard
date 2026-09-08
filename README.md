
  
# Switchboard

Switchboard is a simple database using the Darwin push port feed from RDM. It's not particularly effective, but it gets the job done.

It is hopefully up to date with the specification (such as waiting for HBINIT to rebuild dtabase) and there is support for v19 ready once full support for it is added in RDM (i.e. snapshots still only able to provide v18)

Docker is the best way to use this project in my opinion on a server, but I do not recommend currently using this project in production environments.

## Configuring switchboard

### Step 1: Setting up the environment file

Copy the sample environment file and enter your credentials:

You can acquire your credentials from:
[Darwin Push Port Snapshots](https://raildata.org.uk/dataProduct/P-8b01d5cf-2dd4-48b4-bb98-dc6d3520baf9/overview)
[Darwin Push Port](https://raildata.org.uk/dataProduct/P-d3bf124c-1058-4040-8a62-87181a877d59/overview)

```bash
cp .env.example .env
```

Edit `.env` to configure your PostgreSQL connection and Darwin credentials. You only need to setup PostgreSQL on the machine and then setup a user. Switchboard will manage the database fully.

### Step 2: Retrieving timetable files
For database rebuilds, 'static' timetable files are produced each day. Unfortunately, this needs to be retrieved from [here](https://raildata.org.uk/dataProduct/P-9ca6bc7e-62e1-44d6-b93a-1616f7d2caf8/overview), where there is no support for an API endpoint for retrieval.

You can subscribe to this, go to 'data files' and look at setting up an automatic file transfer. From this (I personally recommend FTP), and modify your config file to point towards this folder.

You will be automatically warned in the logs if you are running off old timetables. I'm not entirely sure when new timetable files are published, so you can disable this behaviour if it's incorrect for your use case.

A segment of the configuration file is found below relating to this:

```toml
[darwin]
timetable_file_path = "data"
warn_about_old_timetables = true
```

### Step 3: Starting the database

I've found that it's most effective to start the database during the scheduled rebuild (02:05am) due to snapshots not providing full data for the day, only for active services.

If you don't fancy 02:05am, running it 5 minutes after the hour is a good idea as it can work off the latest snapshot.

I will not provide support for setting this up as a service (sorry!). I recommend using Docker if you are confused on next steps, found in the next section.


## Running with Docker

Ensure you configure your .env file first.

Start the PostgreSQL database and Switchboard:

```bash
docker compose up -d --build
```

View switchboard logs:

```bash
docker compose logs -f switchboard
```

Stop switchboard:

```bash
docker compose down
```