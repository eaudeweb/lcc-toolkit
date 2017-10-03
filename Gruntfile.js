module.exports = function(grunt) {
    require('jit-grunt')(grunt);
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
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
                    'src/js/lib/jquery.min.js', 'src/js/lib/tether.min.js', 'src/js/lib/bootstrap.js', 'src/js/*js'
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
        uglify: {
            my_target: {
                files: {
                    'static/js/main.js': ['static/js/main.js'],
                    'lcctoolkit/mainapp/static/js/add_articles.js' : ['lcctoolkit/mainapp/static/js/add_articles.js'],
                    'lcctoolkit/mainapp/static/js/legislation_filter.js' : ['lcctoolkit/mainapp/static/js/legislation_filter.js'],
                    'lcctoolkit/mainapp/static/js/login.js' : ['lcctoolkit/mainapp/static/js/login.js'],
                    'lcctoolkit/mainapp/static/js/jquery.validate.js' : ['lcctoolkit/mainapp/static/js/jquery.validate.js']
                }
            }
        }
    });

    grunt.registerTask('default', ['less', 'concat', 'watch']);
    grunt.registerTask('dev', ['less', 'concat']);
    grunt.registerTask('prod', ['less', 'concat', 'uglify']);


};
