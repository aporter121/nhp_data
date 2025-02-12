"""Generate WLI Dataframe"""

import sys

from pyspark import SparkContext
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from inputs_data.helpers import get_spark
from inputs_data.ip.wli import get_ip_wli
from inputs_data.op.wli import get_op_wli


def get_wli(spark: SparkContext = get_spark()) -> DataFrame:
    """Get WLI (combined)

    :param spark: The spark context to use
    :type spark: SparkContext
    :return: The WLI data
    :rtype: DataFrame
    """
    ip = get_ip_wli(spark)
    op = get_op_wli(spark)

    w = Window.partitionBy("provider", "tretspef").orderBy("date")

    successors = spark.read.table("su_data.reference.provider_successors")

    # TODO: this table is generated using a query on our Data Warehouse, but using publically available RTT files
    # ideally this should be made more reproducible
    wl_ac = (
        spark.read.parquet(
            "/Volumes/su_data/nhp/old_nhp_inputs/dev/waiting_list_avg_change.parquet"
        )
        .join(successors, F.col("procode3") == F.col("old_code"))
        .groupBy(F.col("new_code").alias("provider"), F.col("tretspef"), F.col("date"))
        .agg(F.sum("n").alias("n"))
        .withColumn("diff", F.col("n") - F.lag("n", 1).over(w))
        .withColumn(
            "avg_change",
            F.avg("diff").over(
                w.rowsBetween(Window.unboundedPreceding, Window.currentRow)
            ),
        )
        .withColumn("fyear", (F.year("date") - 1) * 100 + (F.year("date") % 100))
        .filter(F.col("fyear") >= 201920)
        .drop("date", "n", "diff")
    )

    return (
        wl_ac.filter(F.col("avg_change") != 0)
        .join(ip, ["fyear", "provider", "tretspef"], "left")
        .join(op, ["fyear", "provider", "tretspef"], "left")
        .fillna(0)
    )


if __name__ == "__main__":
    path = sys.argv[1]

    get_wli().toPandas().to_parquet(f"{path}/wli.parquet")
