module.exports = function(grunt) {
    require('jit-grunt')(grunt);
    grunt.loadNpmTasks('grunt-contrib-concat');

    grunt.initConfig({
        less: {
            development: {
                options: {
                    compress: true,
                    yuicompress: true,
                    optimization: 2
                },
                files: {
                    "static/css/main.css": "src/less/main.less" // destination file and source file
                }
            }
        },
        concat: {
            scripts: {
                src: [
                    'src/js/**/*.js'
                ],
                dest: 'static/js/main.js'
            }
        },
        watch: {
            styles: {
                files: ['src/less/**/*.less'], // which files to watch
                tasks: ['less'],
                options: {
                    nospawn: true
                }
            },
        scripts: {
            files: ['src/js/**/*.js'],
            tasks: ['concat'],
            options: {
                nospawn: true
            }
        }
        },
    });

    grunt.registerTask('default', ['less', 'watch']);
};