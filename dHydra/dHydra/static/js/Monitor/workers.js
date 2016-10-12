var Workers = function(){
	var self = this;
	this.activeOnly = false;
	this.workersInfo = {};
	this.onWatchListChanged = function(){};
	this.workerNames = new Array(); // 全部的worker name
	this.workersWatchList = null; // 要监控的worker name

	this.getWorkersInfoFromRedis = function(){ //从redis中获取开启过的worker
		var self = this;
		$.ajax({
			dataType: "json"
		,	url: "/api/Worker/Monitor/get_workers_from_redis/"
		,	success: function(result){
				if (result["error_code"] == 0){
					self.workersInfo = result["res"];
					console.log(self.workersInfo);
				}	else{
					console.log(result["error_msg"]);
				}
			}
		});
	};

	this.getAllWorkers = function(){ //获取全部worker名
		var self = this;
		$.ajax({
			dataType: "json"
		,	url: "/api/Worker/Monitor/get_worker_names/"
		,	success: function(result){
				if (result["error_code"] == 0){
					self.workerNames = result["res"];
					if (self.workersWatchList == null) {
						self.workersWatchList = result["res"];
						self.onWatchListChanged();
						console.log(self.workersWatchList);
					}
				}	else{
					console.log(result["error_msg"]);
				}
			}
		});
	};

	this.addToWatchList = function(workerName){
		workersWatchList = new Set(this.workersWatchList);
		if (workerName in workersWatchList == false){
			console.log(workersWatchList);
			workersWatchList.add(workerName);
			this.workersWatchList = Array.from(workersWatchList);
			this.onWatchListChanged();
			console.log(this.workersWatchList);
		}
	};

	// 每3秒刷新一下实例信息
	setInterval(function(){
		self.getAllWorkers();
		self.getWorkersInfoFromRedis();
	},3000);
};
