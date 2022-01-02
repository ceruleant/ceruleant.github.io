struct StderrLogger;

impl log::Log for StderrLogger {
    fn enabled(&self, metadata: &log::Metadata) -> bool {
        metadata.level() <= log::Level::Trace
    }

    fn log(&self, record: &log::Record) {
        if self.enabled(record.metadata()) {
            eprintln!("{} {}", record.level(), record.args());
        }
    }

    fn flush(&self) {}
}

static LOGGER: StderrLogger = StderrLogger;

pub fn main() {
    log::set_logger(&LOGGER).expect("Unable to setup logger.");
    log::set_max_level(log::LevelFilter::Trace);
    log::info!("Starting builder...");
    log::info!("Done.");
}
