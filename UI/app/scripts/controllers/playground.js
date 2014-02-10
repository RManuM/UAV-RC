﻿'use strict';

angular.module('uavRcApp')
  .controller('PlaygroundCtrl', function ($scope, socket) {

      socket.forward('CAMERA_PITCH_ANGLE', $scope);
      //socket.forward('ack', $scope);
      $scope.pitchangle = 0;
      $scope.set_pitchangle = function () {
          //socket.emit('CAMERA_PITCH_ANGLE_SET', { pitchangle: $scope.pitchangle });
          //console.time("CAMERA_PITCH_ANGLE")
          var msg = {
              "header": {
                  "msg": {
                      "id": Math.random().toString(36).substring(2, 11),
                      "emitter": "UI",
                      "timestamp": +new Date()
                  }
              },
              "body": {
                  someValue: 1
              }
          };

          console.log("message", msg);

          var callback = function (msg) {
              console.log("callback", msg);
          }
          socket.emit('ack', msg, callback)
      }

      socket.on('ack', function (msg) {
          var ackId = msg.ack;
          msg.header.req = msg.header.msg;
          msg.header.msg = {
              "id": Math.random().toString(36).substring(2, 11),
              "emitter": "UI",
              "timestamp": +new Date()
          }
          msg.ack = true;
          socket.emit(ackId, msg);
      })

      $scope.get_pitchangle = function () {
          socket.emit('CAMERA_PITCH_ANGLE_GET');
      }

      $scope.$on('socket:connect', function (data) {
          console.log("test");
          //console.log(data);
      })

      $scope.$on('socket:CAMERA_PITCH_ANGLE', function (ev, data) {
          console.timeEnd("CAMERA_PITCH_ANGLE");
          $scope.pitchangle = data.pitchangle;
      });


  });
