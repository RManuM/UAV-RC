'use strict';

angular.module('uavRcApp', [
  'ngResource',
  'btford.socket-io',
  'ngRoute'/*,
  'leaflet-directive'*/ //TODO: delete from bower_components (and never try again)
]).
factory('socket', function (socketFactory) {
    var ioSocket = io.connect('http://localhost:8081'); //  || window.location.port ? 'http://localhost:8080' : ''



    var socket = socketFactory({
        ioSocket: ioSocket
    });

    return socket;
}).config(function ($routeProvider) {
    $routeProvider
      .when('/', {
          templateUrl: 'views/main.html',
          controller: 'MainCtrl'
      })
        .when('/playground', {
            templateUrl: 'views/playground.html',
            controller: 'PlaygroundCtrl'
        })
        .when('/ioTest', {
            templateUrl: 'views/ioTest.html',
            controller: 'IoTestCtrl'
        })
        .when('/modules', {
            templateUrl: 'views/modules.html',
            controller: 'ModulesCtrl'
        })
        .when('/debug', {
            templateUrl: 'views/debug.html',
            controller: 'DebugCtrl'
        })
        .otherwise({
            redirectTo: '/'
        });


}).run(function ($rootScope, socket) {

    var onLink = function () {
        console.log("link");
        $rootScope.$apply(function () {
            $rootScope.linked = true;
        });
    }

    var self = {
        id: 'UI',
        signals: {
            ack: true,
            CAM_SET_PITCHANGLE: true,
            COMMAND_GOTO: true,
            GPS_DATA: true,
            _SET: true,
            TRACK: true,
            dummyJSSlot: true,
            dummyPYSlot: true,
            dummySELFSlot: true,
            dummySELFSignal:true,
            CAMERA_PITCH_ANGLE_GET: true,
            CAMERA_PITCH_ANGLE_SET: true
        },
        slots: {
            debug: true,
            ack: true,
            errorack: true,
            GPS_DATA: function (data) {
                //$rootScope.GPS_DATA = data;
                console.log(data);
            },
            dummyJSSignal: true,
            dummyPYSlot: true,
            dummySELFSlot: true,
            dummySELFSignal: true,
            CAMERA_PITCH_ANGLE: true,
            IO_LOG: true
        }
    }

    socket.on('connect', function () {
        var moduleDesc = {
            id: self.id,
            signals: _.keys(self.signals),
            slots: _.keys(self.slots)
        }
        socket.emit('link', moduleDesc, onLink)
    });

    /*_.each(self.slots, function (fn, slot) {
        $rootScope.$on(slot, fn)
    })*/


})
