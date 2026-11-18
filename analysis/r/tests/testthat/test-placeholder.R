test_that("analysis R package placeholder loads", {
  source("../../R/placeholder.R")
  expect_equal(mindbench_name(), "mindbench")
})
