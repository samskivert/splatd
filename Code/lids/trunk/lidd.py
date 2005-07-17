import getopt, sys
import lids
import logging

if __name__ == "__main__":

    conf_file = None
    
    try:
        opts,args = getopt.getopt(sys.argv[1:], "hvf:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt,arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        if opt == "-f":
            conf_file = arg

    # Set up the configuration
    conf = lids.parse_config(conf_file)

    # Set up logging, based on the config file
    logfile = conf.get("daemon.logfile", "lids.log")
    loglevel = conf.get("daemon.loglevel", "info")

    # Set up logging
    if logfile:
        levels = {
                "debug":logging.DEBUG,
                "info":logging.INFO,
                "warning":logging.WARNING,
                "error":logging.ERROR,
                "critical":logging.CRITICAL,
                }

        # Get the lids logger
        logger = logging.getLogger("lids")
        logger.setLevel(levels[loglevel.lower()])

        formatter = logging.Formatter('%(asctime)s %(levelname)-6s %(message)s',
                '%Y%m%d %H:%M:%S')
        log = logging.FileHandler(logfile)
        log.setLevel(levels[loglevel.lower()])
        log.setFormatter(formatter)
        logger.addHandler(log)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)
 

    # Run the daemon
    lids.daemon(conf)

